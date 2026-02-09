"""
Credit-Equity Regime Map Tool
SPX vs CDX IG relationship using detrended equity levels (% deviation from 200d MA)
Includes OLS, Kernel Regression, and Sigmoid regression with beta analysis
"""

import pandas as pd
import numpy as np
import ipywidgets as widgets
from IPython.display import display, HTML, clear_output
from datetime import datetime, timedelta
import bqplot as bqp
from scipy.optimize import minimize
import warnings
warnings.filterwarnings('ignore')

import bql
bq = bql.Service()

# ============================================================================
# DATA LOADING
# ============================================================================

def load_regime_data(start_date, end_date):
    """Load SPX and CDX IG data from Bloomberg"""
    # SPX Index
    spx_request = bql.Request("SPX Index", {
        "PX": bq.data.px_last(dates=bq.func.range(start_date, end_date))
    })
    spx_response = bq.execute(spx_request)
    spx_df = spx_response.single().df().reset_index()
    spx_df = spx_df[["DATE", "PX"]].rename(columns={"PX": "SPX"}).set_index("DATE")

    # CDX IG
    cdx_request = bql.Request("CDX IG CDSI GEN 5Y Corp", {
        "PX": bq.data.px_last(dates=bq.func.range(start_date, end_date))
    })
    cdx_response = bq.execute(cdx_request)
    cdx_df = cdx_response.single().df().reset_index()
    cdx_df = cdx_df[["DATE", "PX"]].rename(columns={"PX": "CDX"}).set_index("DATE")

    # Merge
    df = pd.concat([spx_df, cdx_df], axis=1).dropna()

    # Calculate 200d MA and deviation
    df["SPX_MA200"] = df["SPX"].rolling(window=200).mean()
    df["SPX_DEV"] = ((df["SPX"] / df["SPX_MA200"]) - 1) * 100  # % deviation from MA
    df = df.dropna()

    return df

# ============================================================================
# REGRESSION FUNCTIONS
# ============================================================================

def ols_regression(x, y):
    """Simple OLS linear regression"""
    n = len(x)
    sx = np.sum(x)
    sy = np.sum(y)
    sxy = np.sum(x * y)
    sxx = np.sum(x * x)
    b = (n * sxy - sx * sy) / (n * sxx - sx * sx)
    a = (sy - b * sx) / n
    return {"intercept": a, "slope": b}

def kernel_regression(x_data, y_data, x_grid, bandwidth=4):
    """Nadaraya-Watson kernel regression with Gaussian kernel"""
    y_pred = []
    for xg in x_grid:
        u = (x_data - xg) / bandwidth
        w = np.exp(-0.5 * u * u)
        w_sum = np.sum(w)
        if w_sum > 0:
            y_pred.append(np.sum(w * y_data) / w_sum)
        else:
            y_pred.append(0)
    return np.array(y_pred)

def sigmoid_val(x, params):
    """Sigmoid function: y = floor + (ceiling - floor) / (1 + exp(k * (x - midpoint)))"""
    floor, ceiling, k, midpoint = params
    arg = k * (x - midpoint)
    arg = np.clip(arg, -500, 500)  # Prevent overflow
    exp_term = np.exp(arg)
    return floor + (ceiling - floor) / (1 + exp_term)

def sigmoid_derivative(x, params):
    """Derivative of sigmoid (local beta): dy/dx"""
    floor, ceiling, k, midpoint = params
    arg = k * (x - midpoint)
    arg = np.clip(arg, -500, 500)
    exp_term = np.exp(arg)
    denom = (1 + exp_term) ** 2
    return -(ceiling - floor) * k * exp_term / denom

def fit_sigmoid(x_data, y_data):
    """Fit sigmoid using Nelder-Mead optimization with multi-start"""

    def cost(params):
        floor, ceiling, k, midpoint = params
        # Constraints
        if floor < 38 or floor > 60:
            return 1e15
        if ceiling < 100 or ceiling > 300:
            return 1e15
        if k < 0.05 or k > 2.0:
            return 1e15
        if midpoint < -25 or midpoint > 0:
            return 1e15
        if ceiling - floor < 60:
            return 1e15

        y_pred = sigmoid_val(x_data, params)
        ss = np.sum((y_pred - y_data) ** 2)
        return ss

    # Multi-start optimization
    starts = [
        [48, 170, 0.15, -12],
        [47, 160, 0.20, -10],
        [50, 180, 0.25, -15],
        [46, 200, 0.10, -8],
        [48, 150, 0.30, -18],
        [45, 190, 0.12, -14],
        [49, 170, 0.18, -6],
        [47, 160, 0.35, -20],
        [48, 180, 0.22, -11],
        [50, 200, 0.15, -16],
    ]

    best_result = None
    best_cost = 1e15

    for start in starts:
        result = minimize(cost, start, method='Nelder-Mead',
                         options={'maxiter': 10000, 'xatol': 1e-8, 'fatol': 1e-8})
        if result.fun < best_cost:
            best_cost = result.fun
            best_result = result.x

    return {
        "floor": best_result[0],
        "ceiling": best_result[1],
        "steepness": best_result[2],
        "midpoint": best_result[3]
    }

def kernel_derivative(x_data, y_data, x_point, bandwidth=4, delta=0.01):
    """Numerical derivative of kernel regression at a point"""
    y_minus = kernel_regression(x_data, y_data, [x_point - delta], bandwidth)[0]
    y_plus = kernel_regression(x_data, y_data, [x_point + delta], bandwidth)[0]
    return (y_plus - y_minus) / (2 * delta)

# ============================================================================
# BETA TABLE CALCULATIONS
# ============================================================================

def calculate_beta_table(x_data, y_data, ols_result, sigmoid_params, bandwidth=4):
    """Calculate betas at local and ±1,2,3 std dev points"""
    x_mean = np.mean(x_data)
    x_std = np.std(x_data)

    # Points to evaluate
    points = {
        "Local (Mean)": x_mean,
        "+1 Std Dev": x_mean + x_std,
        "+2 Std Dev": x_mean + 2 * x_std,
        "+3 Std Dev": x_mean + 3 * x_std,
        "-1 Std Dev": x_mean - x_std,
        "-2 Std Dev": x_mean - 2 * x_std,
        "-3 Std Dev": x_mean - 3 * x_std,
    }

    results = []
    for label, x_point in points.items():
        # OLS beta (constant)
        ols_beta = ols_result["slope"]

        # Kernel beta (numerical derivative)
        kernel_beta = kernel_derivative(x_data, y_data, x_point, bandwidth)

        # Sigmoid beta (analytical derivative)
        sig_params = [sigmoid_params["floor"], sigmoid_params["ceiling"],
                      sigmoid_params["steepness"], sigmoid_params["midpoint"]]
        sigmoid_beta = sigmoid_derivative(x_point, sig_params)

        results.append({
            "Point": label,
            "SPX Dev (%)": f"{x_point:.1f}%",
            "OLS Beta": f"{ols_beta:.3f}",
            "Kernel Beta": f"{kernel_beta:.3f}",
            "Sigmoid Beta": f"{sigmoid_beta:.3f}",
        })

    return pd.DataFrame(results)

# ============================================================================
# CHART CREATION (Bloomberg Style)
# ============================================================================

def create_regime_chart(df, ols_result, kernel_y, sigmoid_y, x_grid,
                        show_ols=True, show_kernel=True, show_sigmoid=True):
    """Create Bloomberg-style scatter chart with regression lines"""

    x_data = df["SPX_DEV"].values
    y_data = df["CDX"].values
    dates = df.index

    # Scales
    x_min, x_max = x_grid.min(), x_grid.max()
    y_min = max(35, np.floor(y_data.min() / 5) * 5 - 5)
    y_max = min(200, np.ceil(y_data.max() / 10) * 10 + 10)

    x_scale = bqp.LinearScale(min=x_min, max=x_max)
    y_scale = bqp.LinearScale(min=y_min, max=y_max)

    # Scatter points - color gradient by time (older = lighter)
    n_points = len(x_data)
    colors = np.linspace(0.3, 1.0, n_points)
    color_scale = bqp.ColorScale(colors=["#b0b0b0", "#1a1a2e"])

    scatter = bqp.Scatter(
        x=x_data, y=y_data,
        scales={'x': x_scale, 'y': y_scale, 'color': color_scale},
        color=colors,
        default_size=8,
        opacities=[0.6] * n_points,
        stroke='none'
    )

    marks = [scatter]

    # OLS line (orange, dashed)
    if show_ols:
        ols_y = ols_result["intercept"] + ols_result["slope"] * x_grid
        ols_line = bqp.Lines(
            x=x_grid, y=ols_y,
            scales={'x': x_scale, 'y': y_scale},
            colors=["#f97316"],
            stroke_width=1.5,
            line_style="dashed",
            labels=["OLS"]
        )
        marks.append(ols_line)

    # Kernel line (cyan)
    if show_kernel:
        kernel_line = bqp.Lines(
            x=x_grid, y=kernel_y,
            scales={'x': x_scale, 'y': y_scale},
            colors=["#22d3ee"],
            stroke_width=2.5,
            labels=["Kernel"]
        )
        marks.append(kernel_line)

    # Sigmoid line (purple)
    if show_sigmoid:
        sigmoid_line = bqp.Lines(
            x=x_grid, y=sigmoid_y,
            scales={'x': x_scale, 'y': y_scale},
            colors=["#a78bfa"],
            stroke_width=2.5,
            labels=["Sigmoid"]
        )
        marks.append(sigmoid_line)

    # Zero line (vertical at x=0)
    zero_line = bqp.Lines(
        x=[0, 0], y=[y_min, y_max],
        scales={'x': x_scale, 'y': y_scale},
        colors=["#666666"],
        stroke_width=1,
        line_style="dotted",
        opacities=[0.5]
    )
    marks.append(zero_line)

    # Axes - minimal Bloomberg style
    x_axis = bqp.Axis(
        scale=x_scale,
        label="SPX % Deviation from 200d MA",
        grid_lines="none",
        tick_format=".0f",
        tick_style={'font-size': '10px'}
    )
    y_axis = bqp.Axis(
        scale=y_scale,
        orientation="vertical",
        label="CDX IG (bps)",
        grid_lines="solid",
        grid_color="#e8e8e8",
        tick_format=".0f",
        tick_style={'font-size': '10px'}
    )

    # Figure
    fig = bqp.Figure(
        marks=marks,
        axes=[x_axis, y_axis],
        fig_margin={"top": 40, "bottom": 60, "left": 60, "right": 30},
        background_style={"fill": "#fafafa"},
        title=f"Credit-Equity Regime Map",
        title_style={'font-size': '14px', 'font-weight': 'bold'}
    )
    fig.layout.width = "100%"
    fig.layout.height = "450px"

    # Add tooltip
    tooltip = bqp.Tooltip(fields=['x', 'y'], formats=['.2f', '.1f'],
                          labels=['SPX Dev (%)', 'CDX (bps)'])
    scatter.tooltip = tooltip

    return fig

def create_stats_html(df):
    """Create Bloomberg-style stats box"""
    x_data = df["SPX_DEV"].values
    y_data = df["CDX"].values
    dates = df.index

    first_date = dates[0].strftime("%d%b%y")
    last_date = dates[-1].strftime("%d%b%y")

    # Find high/low CDX with dates
    high_idx = np.argmax(y_data)
    low_idx = np.argmin(y_data)
    high_date = dates[high_idx].strftime("%d%b%y")
    low_date = dates[low_idx].strftime("%d%b%y")

    html = f"""
    <div style="background:#f8f9fa;border:1px solid #dee2e6;border-radius:4px;padding:12px;font-family:monospace;font-size:11px;margin-top:10px;">
        <table style="width:100%;border-collapse:collapse;">
            <tr>
                <td style="padding:2px 8px;"><b>First</b></td>
                <td style="padding:2px 8px;">{first_date}</td>
                <td style="padding:2px 8px;text-align:right;">{y_data[0]:.1f}</td>
                <td style="padding:2px 8px;"><b>Last</b></td>
                <td style="padding:2px 8px;">{last_date}</td>
                <td style="padding:2px 8px;text-align:right;">{y_data[-1]:.1f}</td>
            </tr>
            <tr>
                <td style="padding:2px 8px;"><b>High</b></td>
                <td style="padding:2px 8px;">{high_date}</td>
                <td style="padding:2px 8px;text-align:right;">{y_data[high_idx]:.1f}</td>
                <td style="padding:2px 8px;"><b>Low</b></td>
                <td style="padding:2px 8px;">{low_date}</td>
                <td style="padding:2px 8px;text-align:right;">{y_data[low_idx]:.1f}</td>
            </tr>
            <tr>
                <td style="padding:2px 8px;"><b>Mean</b></td>
                <td colspan="2" style="padding:2px 8px;text-align:right;">{np.mean(y_data):.2f}</td>
                <td style="padding:2px 8px;"><b>Std</b></td>
                <td colspan="2" style="padding:2px 8px;text-align:right;">{np.std(y_data):.2f}</td>
            </tr>
        </table>
    </div>
    """
    return html

# ============================================================================
# MAIN APP STATE AND UI
# ============================================================================

class RegimeMapState:
    def __init__(self):
        self.df = None
        self.ols_result = None
        self.sigmoid_params = None
        self.x_grid = None
        self.kernel_y = None
        self.sigmoid_y = None
        self.bandwidth = 4

state = RegimeMapState()

# Date pickers
start_date = widgets.DatePicker(
    value=(datetime.now() - timedelta(days=365*10)).date(),
    description="Start:"
)
end_date = widgets.DatePicker(
    value=datetime.now().date(),
    description="End:"
)

# Load button
load_btn = widgets.Button(description="Load Data", button_style="primary")
load_output = widgets.Output()

# Regression toggles
show_ols = widgets.Checkbox(value=True, description="OLS (Orange)", indent=False)
show_kernel = widgets.Checkbox(value=True, description="Kernel (Cyan)", indent=False)
show_sigmoid = widgets.Checkbox(value=True, description="Sigmoid (Purple)", indent=False)

# Bandwidth slider
bandwidth_slider = widgets.FloatSlider(
    value=4, min=1, max=10, step=0.5,
    description="Kernel BW:",
    style={'description_width': '80px'},
    layout=widgets.Layout(width="250px")
)

# Sigmoid parameter sliders
sig_floor = widgets.FloatSlider(value=48, min=38, max=60, step=0.5, description="Floor:",
                                 style={'description_width': '70px'}, layout=widgets.Layout(width="220px"))
sig_ceiling = widgets.FloatSlider(value=170, min=100, max=300, step=5, description="Ceiling:",
                                   style={'description_width': '70px'}, layout=widgets.Layout(width="220px"))
sig_steep = widgets.FloatSlider(value=0.15, min=0.05, max=0.5, step=0.01, description="Steepness:",
                                 style={'description_width': '70px'}, layout=widgets.Layout(width="220px"))
sig_mid = widgets.FloatSlider(value=-12, min=-25, max=0, step=0.5, description="Midpoint:",
                               style={'description_width': '70px'}, layout=widgets.Layout(width="220px"))

# Update chart button
update_btn = widgets.Button(description="Update Chart", button_style="info")

# Output areas
chart_output = widgets.Output()
stats_output = widgets.Output()
beta_output = widgets.Output()

def on_load(b):
    with load_output:
        clear_output(wait=True)
        print("Loading data from Bloomberg...")

    try:
        state.df = load_regime_data(
            start_date.value.strftime("%Y-%m-%d"),
            end_date.value.strftime("%Y-%m-%d")
        )

        x_data = state.df["SPX_DEV"].values
        y_data = state.df["CDX"].values

        # Fit regressions
        state.ols_result = ols_regression(x_data, y_data)
        state.sigmoid_params = fit_sigmoid(x_data, y_data)

        # Update sigmoid sliders with fitted values
        sig_floor.value = state.sigmoid_params["floor"]
        sig_ceiling.value = state.sigmoid_params["ceiling"]
        sig_steep.value = state.sigmoid_params["steepness"]
        sig_mid.value = state.sigmoid_params["midpoint"]

        # Create grid and compute curves
        state.x_grid = np.linspace(x_data.min() - 5, x_data.max() + 5, 300)
        state.bandwidth = bandwidth_slider.value
        state.kernel_y = kernel_regression(x_data, y_data, state.x_grid, state.bandwidth)

        sig_params = [state.sigmoid_params["floor"], state.sigmoid_params["ceiling"],
                      state.sigmoid_params["steepness"], state.sigmoid_params["midpoint"]]
        state.sigmoid_y = sigmoid_val(state.x_grid, sig_params)

        with load_output:
            clear_output(wait=True)
            print(f"Loaded {len(state.df)} days from {state.df.index[0].date()} to {state.df.index[-1].date()}")
            print(f"Sigmoid fit: floor={state.sigmoid_params['floor']:.1f}, ceiling={state.sigmoid_params['ceiling']:.1f}, "
                  f"steepness={state.sigmoid_params['steepness']:.3f}, midpoint={state.sigmoid_params['midpoint']:.1f}")

        update_display()

    except Exception as e:
        with load_output:
            clear_output(wait=True)
            print(f"Error: {e}")

def update_display():
    if state.df is None:
        return

    x_data = state.df["SPX_DEV"].values
    y_data = state.df["CDX"].values

    # Recalculate with current slider values
    state.bandwidth = bandwidth_slider.value
    state.kernel_y = kernel_regression(x_data, y_data, state.x_grid, state.bandwidth)

    sig_params = [sig_floor.value, sig_ceiling.value, sig_steep.value, sig_mid.value]
    state.sigmoid_y = sigmoid_val(state.x_grid, sig_params)

    # Update chart
    with chart_output:
        clear_output(wait=True)
        fig = create_regime_chart(
            state.df, state.ols_result, state.kernel_y, state.sigmoid_y, state.x_grid,
            show_ols=show_ols.value, show_kernel=show_kernel.value, show_sigmoid=show_sigmoid.value
        )
        display(fig)

    # Update stats
    with stats_output:
        clear_output(wait=True)
        display(HTML(create_stats_html(state.df)))

    # Update beta table
    with beta_output:
        clear_output(wait=True)
        sigmoid_params_dict = {
            "floor": sig_floor.value,
            "ceiling": sig_ceiling.value,
            "steepness": sig_steep.value,
            "midpoint": sig_mid.value
        }
        beta_df = calculate_beta_table(x_data, y_data, state.ols_result,
                                        sigmoid_params_dict, state.bandwidth)
        display(HTML("<h4 style='margin:10px 0 5px 0;'>Beta Analysis (bps per 1% SPX move)</h4>"))
        display(beta_df.style.set_properties(**{
            'text-align': 'center',
            'font-size': '11px'
        }).set_table_styles([
            {'selector': 'th', 'props': [('text-align', 'center'), ('font-size', '11px'), ('background', '#f0f0f0')]}
        ]))

def on_update(b):
    update_display()

# Connect callbacks
load_btn.on_click(on_load)
update_btn.on_click(on_update)
show_ols.observe(lambda change: update_display(), names='value')
show_kernel.observe(lambda change: update_display(), names='value')
show_sigmoid.observe(lambda change: update_display(), names='value')

# Layout
controls_row1 = widgets.HBox([start_date, end_date, load_btn])
controls_row2 = widgets.HBox([show_ols, show_kernel, show_sigmoid, bandwidth_slider])
sig_controls = widgets.VBox([
    widgets.HTML("<b style='font-size:12px;color:#a78bfa;'>Sigmoid Parameters</b>"),
    widgets.HBox([sig_floor, sig_ceiling]),
    widgets.HBox([sig_steep, sig_mid]),
])
controls_row3 = widgets.HBox([sig_controls, update_btn])

app = widgets.VBox([
    widgets.HTML("<h2 style='color:#264653;margin-bottom:10px;'>Credit-Equity Regime Map</h2>"),
    controls_row1,
    load_output,
    controls_row2,
    controls_row3,
    chart_output,
    stats_output,
    beta_output,
])

display(app)

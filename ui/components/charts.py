"""Plotly chart components for squeeze visualization"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np


def create_squeeze_chart(df: pd.DataFrame, symbol: str,
                         show_200_dma: bool = True,
                         show_50_dma: bool = True,
                         show_breakout_markers: bool = True) -> go.Figure:
    """
    Create interactive chart with candlesticks, BB, KC, squeeze indicators,
    DMA lines, and breakout markers.

    Args:
        df: DataFrame with OHLCV and indicator data
        symbol: Stock symbol for title
        show_200_dma: Whether to show 200 DMA line
        show_50_dma: Whether to show 50 DMA line
        show_breakout_markers: Whether to show breakout markers

    Returns:
        Plotly Figure object
    """
    # Calculate 50 DMA if not present
    if 'DMA_50' not in df.columns:
        df = df.copy()
        df['DMA_50'] = df['Close'].rolling(window=50).mean()

    # Create subplots
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.6, 0.2, 0.2],
        subplot_titles=(f'{symbol} Price with Bollinger Bands & Keltner Channels',
                       'Volume', 'Squeeze Momentum')
    )

    # Get date column
    x_data = df['Date'] if 'Date' in df.columns else df.index

    # Candlestick chart
    fig.add_trace(go.Candlestick(
        x=x_data,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Price',
        increasing_line_color='#00D26A',
        decreasing_line_color='#FF4B4B'
    ), row=1, col=1)

    # Bollinger Bands
    fig.add_trace(go.Scatter(
        x=x_data,
        y=df['BB_Upper'],
        line=dict(color='rgba(30, 144, 255, 0.7)', width=1),
        name='BB Upper',
        showlegend=True
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=x_data,
        y=df['BB_Lower'],
        fill='tonexty',
        fillcolor='rgba(30, 144, 255, 0.1)',
        line=dict(color='rgba(30, 144, 255, 0.7)', width=1),
        name='BB Lower',
        showlegend=True
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=x_data,
        y=df['BB_Middle'],
        line=dict(color='rgba(30, 144, 255, 0.9)', width=1, dash='dot'),
        name='BB Middle',
        showlegend=True
    ), row=1, col=1)

    # Keltner Channels
    fig.add_trace(go.Scatter(
        x=x_data,
        y=df['KC_Upper'],
        line=dict(color='rgba(255, 140, 0, 0.8)', width=1, dash='dash'),
        name='KC Upper',
        showlegend=True
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=x_data,
        y=df['KC_Lower'],
        line=dict(color='rgba(255, 140, 0, 0.8)', width=1, dash='dash'),
        name='KC Lower',
        showlegend=True
    ), row=1, col=1)

    # Squeeze dots at bottom of price chart
    price_min = df['Low'].min() * 0.995

    squeeze_on = df[df['Squeeze_On'] == True]
    squeeze_off = df[df['Squeeze_Off'] == True]

    squeeze_on_x = squeeze_on['Date'] if 'Date' in squeeze_on.columns else squeeze_on.index
    squeeze_off_x = squeeze_off['Date'] if 'Date' in squeeze_off.columns else squeeze_off.index

    fig.add_trace(go.Scatter(
        x=squeeze_on_x,
        y=[price_min] * len(squeeze_on),
        mode='markers',
        marker=dict(color='#00D26A', size=8, symbol='circle'),
        name='Squeeze ON',
        showlegend=True
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=squeeze_off_x,
        y=[price_min] * len(squeeze_off),
        mode='markers',
        marker=dict(color='#FF4B4B', size=8, symbol='circle'),
        name='Squeeze OFF',
        showlegend=True
    ), row=1, col=1)

    # Volume bars
    colors = ['#00D26A' if c >= o else '#FF4B4B'
              for c, o in zip(df['Close'], df['Open'])]

    fig.add_trace(go.Bar(
        x=x_data,
        y=df['Volume'],
        marker_color=colors,
        name='Volume',
        showlegend=False
    ), row=2, col=1)

    # Squeeze Momentum histogram
    if 'Squeeze_Momentum' in df.columns:
        momentum_colors = []
        prev_momentum = 0

        for i, row in df.iterrows():
            m = row['Squeeze_Momentum']
            if pd.isna(m):
                momentum_colors.append('#888888')
            elif m > 0:
                if m > prev_momentum:
                    momentum_colors.append('#00FF7F')  # Lime - bullish increasing
                else:
                    momentum_colors.append('#006400')  # Dark green - bullish decreasing
            else:
                if m < prev_momentum:
                    momentum_colors.append('#FF0000')  # Red - bearish increasing
                else:
                    momentum_colors.append('#8B0000')  # Dark red - bearish decreasing
            prev_momentum = m if not pd.isna(m) else prev_momentum

        fig.add_trace(go.Bar(
            x=x_data,
            y=df['Squeeze_Momentum'],
            marker_color=momentum_colors,
            name='Momentum',
            showlegend=False
        ), row=3, col=1)

    # Add 200 DMA line
    if show_200_dma and 'DMA_200' in df.columns:
        dma_200_valid = df[df['DMA_200'].notna()]
        if not dma_200_valid.empty:
            dma_200_x = dma_200_valid['Date'] if 'Date' in dma_200_valid.columns else dma_200_valid.index
            fig.add_trace(go.Scatter(
                x=dma_200_x,
                y=dma_200_valid['DMA_200'],
                mode='lines',
                name='200 DMA',
                line=dict(color='#0080FF', width=2, dash='dash'),
                hovertemplate='200 DMA: ₹%{y:.2f}<extra></extra>',
                showlegend=True
            ), row=1, col=1)

    # Add 50 DMA line
    if show_50_dma and 'DMA_50' in df.columns:
        dma_50_valid = df[df['DMA_50'].notna()]
        if not dma_50_valid.empty:
            dma_50_x = dma_50_valid['Date'] if 'Date' in dma_50_valid.columns else dma_50_valid.index
            fig.add_trace(go.Scatter(
                x=dma_50_x,
                y=dma_50_valid['DMA_50'],
                mode='lines',
                name='50 DMA',
                line=dict(color='#FFA500', width=2, dash='dot'),
                hovertemplate='50 DMA: ₹%{y:.2f}<extra></extra>',
                showlegend=True
            ), row=1, col=1)

    # Add breakout markers
    if show_breakout_markers and 'Squeeze_Fire' in df.columns:
        # Get breakout points (where squeeze fires)
        breakouts = df[df['Squeeze_Fire'] == True].copy()

        if not breakouts.empty:
            breakout_x = breakouts['Date'] if 'Date' in breakouts.columns else breakouts.index

            # CRITICAL: Separate bullish and bearish breakouts based on momentum AND 200 DMA position
            # Bullish breakout ONLY if momentum > 0 AND price > 200 DMA
            # Bearish breakout ONLY if momentum < 0 AND price < 200 DMA
            if 'DMA_200' in breakouts.columns:
                bullish_breakouts = breakouts[
                    (breakouts['Squeeze_Momentum'] > 0) &
                    (breakouts['DMA_200'].notna()) &
                    (breakouts['Close'] > breakouts['DMA_200'])
                ]
                bearish_breakouts = breakouts[
                    (breakouts['Squeeze_Momentum'] < 0) &
                    (breakouts['DMA_200'].notna()) &
                    (breakouts['Close'] < breakouts['DMA_200'])
                ]
            else:
                # Fallback when 200 DMA not available (less reliable)
                bullish_breakouts = breakouts[breakouts['Squeeze_Momentum'] > 0]
                bearish_breakouts = breakouts[breakouts['Squeeze_Momentum'] <= 0]

            # Bullish breakout markers
            if not bullish_breakouts.empty:
                bullish_x = bullish_breakouts['Date'] if 'Date' in bullish_breakouts.columns else bullish_breakouts.index

                # Prepare custom data for hover
                customdata = []
                for idx, row in bullish_breakouts.iterrows():
                    above_200 = 'Yes' if 'DMA_200' in row and pd.notna(row['DMA_200']) and row['Close'] > row['DMA_200'] else 'N/A'
                    above_50 = 'Yes' if 'DMA_50' in row and pd.notna(row['DMA_50']) and row['Close'] > row['DMA_50'] else 'N/A'
                    customdata.append([
                        row['Close'],
                        row['BB_Width'] if 'BB_Width' in row and pd.notna(row['BB_Width']) else 0,
                        row['Volume'] if 'Volume' in row else 0,
                        above_200,
                        above_50
                    ])

                fig.add_trace(go.Scatter(
                    x=bullish_x,
                    y=bullish_breakouts['High'] * 1.02,
                    mode='markers+text',
                    marker=dict(
                        symbol='triangle-up',
                        size=14,
                        color='#00AA00',
                        line=dict(color='#004400', width=2)
                    ),
                    text=['B'] * len(bullish_breakouts),
                    textposition='top center',
                    textfont=dict(size=9, color='white', family='Arial Black'),
                    name='Bullish Breakout',
                    hovertemplate=(
                        '<b>Bullish Breakout</b><br>' +
                        'Date: %{x}<br>' +
                        'Price: ₹%{customdata[0]:.2f}<br>' +
                        'BB Width: %{customdata[1]:.2f}%<br>' +
                        'Volume: %{customdata[2]:,}<br>' +
                        'Above 200 DMA: %{customdata[3]}<br>' +
                        'Above 50 DMA: %{customdata[4]}<br>' +
                        '<extra></extra>'
                    ),
                    customdata=customdata,
                    showlegend=True
                ), row=1, col=1)

            # Bearish breakout markers
            if not bearish_breakouts.empty:
                bearish_x = bearish_breakouts['Date'] if 'Date' in bearish_breakouts.columns else bearish_breakouts.index

                # Prepare custom data for hover
                customdata = []
                for idx, row in bearish_breakouts.iterrows():
                    below_200 = 'Yes' if 'DMA_200' in row and pd.notna(row['DMA_200']) and row['Close'] < row['DMA_200'] else 'N/A'
                    below_50 = 'Yes' if 'DMA_50' in row and pd.notna(row['DMA_50']) and row['Close'] < row['DMA_50'] else 'N/A'
                    customdata.append([
                        row['Close'],
                        row['BB_Width'] if 'BB_Width' in row and pd.notna(row['BB_Width']) else 0,
                        row['Volume'] if 'Volume' in row else 0,
                        below_200,
                        below_50
                    ])

                fig.add_trace(go.Scatter(
                    x=bearish_x,
                    y=bearish_breakouts['Low'] * 0.98,
                    mode='markers+text',
                    marker=dict(
                        symbol='triangle-down',
                        size=14,
                        color='#DD0000',
                        line=dict(color='#660000', width=2)
                    ),
                    text=['S'] * len(bearish_breakouts),
                    textposition='bottom center',
                    textfont=dict(size=9, color='white', family='Arial Black'),
                    name='Bearish Breakout',
                    hovertemplate=(
                        '<b>Bearish Breakout</b><br>' +
                        'Date: %{x}<br>' +
                        'Price: ₹%{customdata[0]:.2f}<br>' +
                        'BB Width: %{customdata[1]:.2f}%<br>' +
                        'Volume: %{customdata[2]:,}<br>' +
                        'Below 200 DMA: %{customdata[3]}<br>' +
                        'Below 50 DMA: %{customdata[4]}<br>' +
                        '<extra></extra>'
                    ),
                    customdata=customdata,
                    showlegend=True
                ), row=1, col=1)

    # Update layout
    fig.update_layout(
        template='plotly_dark',
        height=800,
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.02,
            bgcolor='rgba(0,0,0,0.5)'
        ),
        xaxis_rangeslider_visible=False,
        paper_bgcolor='#0E1117',
        plot_bgcolor='#0E1117',
        font=dict(color='white')
    )

    # Update axes
    fig.update_xaxes(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
    fig.update_yaxes(showgrid=True, gridcolor='rgba(128,128,128,0.2)')

    return fig


def create_mini_chart(df: pd.DataFrame, show_squeeze: bool = True) -> go.Figure:
    """
    Create a mini chart for table/card display.

    Args:
        df: DataFrame with price data
        show_squeeze: Whether to show squeeze indicators

    Returns:
        Plotly Figure object
    """
    x_data = df['Date'] if 'Date' in df.columns else df.index

    # Determine if bullish or bearish overall
    first_close = df['Close'].iloc[0]
    last_close = df['Close'].iloc[-1]
    color = '#00D26A' if last_close >= first_close else '#FF4B4B'

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=x_data,
        y=df['Close'],
        mode='lines',
        line=dict(color=color, width=2),
        fill='tozeroy',
        fillcolor=f'rgba{tuple(list(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)) + [0.1])}'
    ))

    fig.update_layout(
        height=100,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False)
    )

    return fig


def create_squeeze_duration_chart(events: list) -> go.Figure:
    """
    Create a bar chart showing squeeze durations with human-readable labels.

    Args:
        events: List of squeeze events

    Returns:
        Plotly Figure object
    """
    if not events:
        fig = go.Figure()
        fig.add_annotation(
            text="No squeeze history available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color='white')
        )
        fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='#0E1117',
            plot_bgcolor='#0E1117',
        )
        return fig

    df = pd.DataFrame(events)

    colors = ['#00D26A' if d == 'BULLISH' else '#FF4B4B' if d == 'BEARISH' else '#888888'
              for d in df['direction']]

    # Create human-readable duration labels
    duration_labels = [f"{d} Days" if d != 1 else "1 Day" for d in df['duration']]

    # Format dates for x-axis labels
    try:
        x_labels = [pd.to_datetime(d).strftime('%b %d, %Y') if d != 'Ongoing' else 'Ongoing'
                   for d in df['start_date']]
    except:
        x_labels = [str(d) for d in df['start_date']]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=x_labels,
        y=df['duration'],
        marker_color=colors,
        text=duration_labels,
        textposition='outside',
        textfont=dict(size=11, color='white'),
        hovertemplate=(
            '<b>Squeeze Event</b><br>' +
            'Start Date: %{x}<br>' +
            'Duration: %{text}<br>' +
            'Direction: %{customdata}<br>' +
            '<extra></extra>'
        ),
        customdata=df['direction']
    ))

    fig.update_layout(
        title=dict(
            text='Squeeze Duration (Days)',
            font=dict(size=16, color='white'),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title=dict(
                text='Squeeze Start Date',
                font=dict(size=12, color='#B8BCC4')
            ),
            tickangle=-45,
            tickfont=dict(size=10, color='#E8EAED'),
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)'
        ),
        yaxis=dict(
            title=dict(
                text='Duration (Days)',
                font=dict(size=12, color='#B8BCC4')
            ),
            tickfont=dict(size=10, color='#E8EAED'),
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)',
            ticksuffix=' days'
        ),
        template='plotly_dark',
        height=350,
        paper_bgcolor='#0E1117',
        plot_bgcolor='#0E1117',
        margin=dict(l=60, r=20, t=50, b=80),
        showlegend=False
    )

    # Add average line if multiple events
    if len(df) > 1:
        avg_duration = df['duration'].mean()
        fig.add_hline(
            y=avg_duration,
            line_dash='dash',
            line_color='rgba(255,255,255,0.5)',
            annotation_text=f'Avg: {avg_duration:.1f} days',
            annotation_position='top right',
            annotation_font=dict(size=10, color='#B8BCC4')
        )

    return fig


def create_summary_gauge(value: int, max_value: int, title: str,
                        color: str = '#1E90FF') -> go.Figure:
    """
    Create a gauge chart for summary metrics.

    Args:
        value: Current value
        max_value: Maximum value for gauge
        title: Gauge title
        color: Gauge color

    Returns:
        Plotly Figure object
    """
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title, 'font': {'size': 14, 'color': 'white'}},
        gauge={
            'axis': {'range': [0, max_value], 'tickcolor': 'white'},
            'bar': {'color': color},
            'bgcolor': '#262730',
            'borderwidth': 0,
            'steps': [
                {'range': [0, max_value * 0.5], 'color': 'rgba(128,128,128,0.2)'},
                {'range': [max_value * 0.5, max_value], 'color': 'rgba(128,128,128,0.3)'}
            ]
        },
        number={'font': {'color': 'white', 'size': 24}}
    ))

    fig.update_layout(
        height=200,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )

    return fig

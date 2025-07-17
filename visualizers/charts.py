import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List, Any
import numpy as np


class ChartGenerator:
    """Generate interactive charts for Terraform plan visualization"""

    def __init__(self):
        # Color schemes
        self.action_colors = {
            'create': '#4CAF50',  # Green
            'update': '#2196F3',  # Blue
            'delete': '#F44336'  # Red
        }

        self.risk_colors = {
            'Low': '#4CAF50',
            'Medium': '#FF9800',
            'High': '#F44336'
        }

        # Default plotly template
        self.template = 'plotly_white'

    def create_resource_type_pie(self, resource_types: Dict[str, int]) -> go.Figure:
        """Create a pie chart showing resource type distribution"""
        if not resource_types:
            return self._create_empty_chart("No resource type data available")

        # Sort by count and take top 10 to avoid clutter
        sorted_types = dict(sorted(resource_types.items(), key=lambda x: x[1], reverse=True)[:10])

        labels = list(sorted_types.keys())
        values = list(sorted_types.values())

        # Generate colors
        colors = px.colors.qualitative.Set3[:len(labels)]

        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            marker=dict(colors=colors, line=dict(color='#FFFFFF', width=2)),
            textposition="inside",
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>" +
                          "Count: %{value}<br>" +
                          "Percentage: %{percent}<br>" +
                          "<extra></extra>"
        )])

        fig.update_layout(
            title=dict(
                text="Resource Types Distribution",
                x=0.5,
                font=dict(size=16, family="Arial, sans-serif")
            ),
            template=self.template,
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.01
            ),
            margin=dict(t=50, b=50, l=50, r=50),
            height=400
        )

        return fig

    def create_change_actions_bar(self, summary: Dict[str, int]) -> go.Figure:
        """Create a bar chart showing change actions"""
        actions = ['create', 'update', 'delete']
        values = [summary.get(action, 0) for action in actions]
        colors = [self.action_colors[action] for action in actions]

        fig = go.Figure(data=[
            go.Bar(
                x=actions,
                y=values,
                marker_color=colors,
                text=values,
                textposition='auto',
                hovertemplate="<b>%{x}</b><br>" +
                              "Count: %{y}<br>" +
                              "<extra></extra>"
            )
        ])

        fig.update_layout(
            title=dict(
                text="Planned Changes by Action",
                x=0.5,
                font=dict(size=16, family="Arial, sans-serif")
            ),
            xaxis_title="Action Type",
            yaxis_title="Number of Resources",
            template=self.template,
            showlegend=False,
            margin=dict(t=50, b=50, l=50, r=50),
            height=400
        )

        # Add annotations for zero values
        for i, (action, value) in enumerate(zip(actions, values)):
            if value == 0:
                fig.add_annotation(
                    x=action,
                    y=0.1,
                    text="No changes",
                    showarrow=False,
                    font=dict(color="gray", size=10)
                )

        return fig

    def create_risk_heatmap(self, risk_by_type: Dict[str, Dict[str, int]]) -> go.Figure:
        """Create a heatmap showing risk levels by resource type"""
        if not risk_by_type:
            return self._create_empty_chart("No risk data available")

        # Prepare data for heatmap
        resource_types = list(risk_by_type.keys())
        risk_levels = ['Low', 'Medium', 'High']

        # Create matrix
        z_data = []
        hover_text = []

        for risk_level in risk_levels:
            row = []
            hover_row = []
            for resource_type in resource_types:
                count = risk_by_type.get(resource_type, {}).get(risk_level, 0)
                row.append(count)
                hover_row.append(f"Type: {resource_type}<br>Risk: {risk_level}<br>Count: {count}")
            z_data.append(row)
            hover_text.append(hover_row)

        fig = go.Figure(data=go.Heatmap(
            z=z_data,
            x=resource_types,
            y=risk_levels,
            colorscale=[[0, '#E8F5E8'], [0.5, '#FFF3CD'], [1, '#F8D7DA']],
            text=z_data,
            texttemplate="%{text}",
            textfont={"size": 12},
            hovertemplate="%{text}<extra></extra>",
            showscale=True,
            colorbar=dict(title="Count")
        ))

        fig.update_layout(
            title=dict(
                text="Risk Assessment by Resource Type",
                x=0.5,
                font=dict(size=16, family="Arial, sans-serif")
            ),
            xaxis_title="Resource Type",
            yaxis_title="Risk Level",
            template=self.template,
            height=400,
            margin=dict(t=50, b=100, l=50, r=50)
        )

        # Rotate x-axis labels if too many
        if len(resource_types) > 5:
            fig.update_xaxes(tickangle=45)

        return fig

    def create_change_timeline(self, changes_by_action: Dict[str, int]) -> go.Figure:
        """Create a timeline-style visualization of changes"""
        actions = list(changes_by_action.keys())
        values = list(changes_by_action.values())

        # Create a waterfall-like chart
        fig = go.Figure()

        cumulative = 0
        for i, (action, value) in enumerate(zip(actions, values)):
            fig.add_trace(go.Bar(
                name=action.title(),
                x=[action],
                y=[value],
                marker_color=self.action_colors.get(action, '#666666'),
                text=f"{value}",
                textposition='auto',
                hovertemplate=f"<b>{action.title()}</b><br>Count: {value}<extra></extra>"
            ))

        fig.update_layout(
            title=dict(
                text="Change Distribution",
                x=0.5,
                font=dict(size=16, family="Arial, sans-serif")
            ),
            xaxis_title="Action Type",
            yaxis_title="Number of Resources",
            template=self.template,
            showlegend=True,
            barmode='group',
            height=400
        )

        return fig

    def create_resource_impact_matrix(self, resource_data: List[Dict[str, Any]]) -> go.Figure:
        """Create a matrix showing resource impact levels"""
        if not resource_data:
            return self._create_empty_chart("No resource data available")

        # Create impact matrix data
        df = pd.DataFrame(resource_data)

        # Group by resource type and action
        impact_matrix = df.groupby(['type', 'action']).size().reset_index(name='count')

        # Pivot for heatmap
        pivot_df = impact_matrix.pivot(index='type', columns='action', values='count').fillna(0)

        fig = go.Figure(data=go.Heatmap(
            z=pivot_df.values,
            x=pivot_df.columns,
            y=pivot_df.index,
            colorscale='RdYlGn_r',
            text=pivot_df.values,
            texttemplate="%{text}",
            textfont={"size": 10},
            hovertemplate="Type: %{y}<br>Action: %{x}<br>Count: %{text}<extra></extra>"
        ))

        fig.update_layout(
            title=dict(
                text="Resource Impact Matrix",
                x=0.5,
                font=dict(size=16, family="Arial, sans-serif")
            ),
            xaxis_title="Action",
            yaxis_title="Resource Type",
            template=self.template,
            height=max(400, len(pivot_df.index) * 30),
            margin=dict(t=50, b=50, l=150, r=50)
        )

        return fig

    def create_summary_gauge(self, risk_score: int, title: str = "Risk Score") -> go.Figure:
        """Create a gauge chart for risk score"""
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=risk_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': title},
            delta={'reference': 50},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 30], 'color': "lightgreen"},
                    {'range': [30, 70], 'color': "yellow"},
                    {'range': [70, 100], 'color': "lightcoral"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))

        fig.update_layout(
            template=self.template,
            height=300,
            margin=dict(t=50, b=50, l=50, r=50)
        )

        return fig

    def create_change_flow_sankey(self, before_after_data: List[Dict[str, Any]]) -> go.Figure:
        """Create a Sankey diagram showing resource state transitions"""
        if not before_after_data:
            return self._create_empty_chart("No state transition data available")

        # Simplified Sankey - this would need more complex logic for real implementation
        # For now, create a basic flow chart

        sources = []
        targets = []
        values = []
        labels = ["Current State", "Planned State"]

        # Add basic flow logic here
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=labels,
                color="blue"
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values
            )
        )])

        fig.update_layout(
            title_text="Resource State Flow",
            font_size=10,
            template=self.template,
            height=400
        )

        return fig

    def _create_empty_chart(self, message: str) -> go.Figure:
        """Create an empty chart with a message"""
        fig = go.Figure()

        fig.add_annotation(
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            text=message,
            showarrow=False,
            font=dict(size=16, color="gray")
        )

        fig.update_layout(
            template=self.template,
            height=400,
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False)
        )

        return fig

    def create_resource_count_trend(self, summary: Dict[str, int]) -> go.Figure:
        """Create a simple trend visualization"""
        actions = ['create', 'update', 'delete']
        values = [summary.get(action, 0) for action in actions]
        colors = [self.action_colors[action] for action in actions]

        fig = go.Figure()

        # Add bars
        fig.add_trace(go.Bar(
            x=actions,
            y=values,
            marker_color=colors,
            text=values,
            textposition='auto',
            name="Resource Changes"
        ))

        # Add trend line (simplified)
        if max(values) > 0:
            fig.add_trace(go.Scatter(
                x=actions,
                y=values,
                mode='lines+markers',
                line=dict(color='orange', width=3),
                marker=dict(size=8),
                name="Trend"
            ))

        fig.update_layout(
            title=dict(
                text="Change Distribution with Trend",
                x=0.5,
                font=dict(size=16, family="Arial, sans-serif")
            ),
            xaxis_title="Action Type",
            yaxis_title="Count",
            template=self.template,
            showlegend=True,
            height=400
        )

        return fig
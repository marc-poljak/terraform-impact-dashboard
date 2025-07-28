import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List, Any
import numpy as np


class ChartGenerator:
    """Enhanced chart generator with multi-cloud support for Terraform plan visualization"""

    def __init__(self):
        # Enhanced color schemes for multi-cloud
        self.action_colors = {
            'create': '#4CAF50',  # Green
            'update': '#2196F3',  # Blue
            'delete': '#F44336',  # Red
            'replace': '#FF9800'  # Orange
        }

        self.risk_colors = {
            'Low': '#4CAF50',
            'Medium': '#FF9800',
            'High': '#F44336'
        }

        # Provider-specific colors
        self.provider_colors = {
            'aws': '#FF9900',  # AWS Orange
            'azure': '#0078D4',  # Azure Blue
            'google': '#4285F4',  # Google Blue
            'kubernetes': '#326CE5',  # Kubernetes Blue
            'terraform': '#623CE4',  # Terraform Purple
            'unknown': '#666666'  # Gray
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

    def create_provider_distribution_pie(self, provider_counts: Dict[str, int]) -> go.Figure:
        """Create a pie chart showing cloud provider distribution (NEW)"""
        if not provider_counts:
            return self._create_empty_chart("No provider data available")

        # Filter out 'unknown' and 'other' if they're small
        filtered_providers = {k: v for k, v in provider_counts.items() if k not in ['unknown', 'other'] or v > 1}

        if not filtered_providers:
            return self._create_empty_chart("No cloud provider data available")

        labels = list(filtered_providers.keys())
        values = list(filtered_providers.values())

        # Use provider-specific colors
        colors = [self.provider_colors.get(provider, '#666666') for provider in labels]

        fig = go.Figure(data=[go.Pie(
            labels=[provider.upper() for provider in labels],
            values=values,
            hole=0.3,
            marker=dict(colors=colors, line=dict(color='#FFFFFF', width=2)),
            textposition="inside",
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>" +
                          "Resources: %{value}<br>" +
                          "Percentage: %{percent}<br>" +
                          "<extra></extra>"
        )])

        fig.update_layout(
            title=dict(
                text="Cloud Provider Distribution",
                x=0.5,
                font=dict(size=16, family="Arial, sans-serif")
            ),
            template=self.template,
            showlegend=True,
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

    def create_provider_actions_stacked_bar(self, actions_by_provider: Dict[str, Dict[str, int]]) -> go.Figure:
        """Create a stacked bar chart showing actions by provider (NEW)"""
        if not actions_by_provider:
            return self._create_empty_chart("No provider action data available")

        providers = list(actions_by_provider.keys())
        actions = ['create', 'update', 'delete']

        fig = go.Figure()

        for action in actions:
            values = [actions_by_provider[provider].get(action, 0) for provider in providers]
            fig.add_trace(go.Bar(
                name=action.title(),
                x=[p.upper() for p in providers],
                y=values,
                marker_color=self.action_colors[action],
                hovertemplate=f"<b>{action.title()}</b><br>" +
                              "Provider: %{x}<br>" +
                              "Count: %{y}<br>" +
                              "<extra></extra>"
            ))

        fig.update_layout(
            title=dict(
                text="Actions by Cloud Provider",
                x=0.5,
                font=dict(size=16, family="Arial, sans-serif")
            ),
            xaxis_title="Cloud Provider",
            yaxis_title="Number of Resources",
            template=self.template,
            barmode='stack',
            height=400
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

    def create_provider_risk_comparison(self, provider_risk_data: Dict[str, Dict[str, Any]]) -> go.Figure:
        """Create a comparison chart of risk levels across providers (NEW)"""
        if not provider_risk_data:
            return self._create_empty_chart("No provider risk data available")

        providers = list(provider_risk_data.keys())
        risk_levels = ['Low', 'Medium', 'High']

        fig = go.Figure()

        for risk_level in risk_levels:
            values = []
            for provider in providers:
                # Get count for this risk level, default to 0
                count = 0
                if f'{risk_level.lower()}_risk_count' in provider_risk_data[provider]:
                    count = provider_risk_data[provider][f'{risk_level.lower()}_risk_count']
                elif f'{risk_level}_risk_count' in provider_risk_data[provider]:
                    count = provider_risk_data[provider][f'{risk_level}_risk_count']
                values.append(count)

            fig.add_trace(go.Bar(
                name=f'{risk_level} Risk',
                x=[p.upper() for p in providers],
                y=values,
                marker_color=self.risk_colors[risk_level],
                hovertemplate=f"<b>{risk_level} Risk</b><br>" +
                              "Provider: %{x}<br>" +
                              "Count: %{y}<br>" +
                              "<extra></extra>"
            ))

        fig.update_layout(
            title=dict(
                text="Risk Levels by Cloud Provider",
                x=0.5,
                font=dict(size=16, family="Arial, sans-serif")
            ),
            xaxis_title="Cloud Provider",
            yaxis_title="Number of Resources",
            template=self.template,
            barmode='stack',
            height=400
        )

        return fig

    def create_multi_cloud_overview_dashboard(self, provider_data: Dict[str, Any]) -> go.Figure:
        """Create a comprehensive multi-cloud overview dashboard (NEW)"""
        if not provider_data:
            return self._create_empty_chart("No multi-cloud data available")

        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Provider Distribution', 'Risk by Provider',
                            'Resource Count by Provider', 'Actions by Provider'),
            specs=[[{"type": "pie"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "bar"}]]
        )

        # Provider distribution (pie chart)
        if 'provider_counts' in provider_data:
            providers = list(provider_data['provider_counts'].keys())
            counts = list(provider_data['provider_counts'].values())
            colors = [self.provider_colors.get(p, '#666666') for p in providers]

            fig.add_trace(
                go.Pie(labels=[p.upper() for p in providers], values=counts,
                       marker=dict(colors=colors), name="Providers"),
                row=1, col=1
            )

        # Risk by provider (stacked bar)
        if 'provider_risk_summary' in provider_data:
            providers = list(provider_data['provider_risk_summary'].keys())
            risk_levels = ['high_risk_count', 'medium_risk_count', 'low_risk_count']
            risk_names = ['High', 'Medium', 'Low']

            for i, (risk_level, risk_name) in enumerate(zip(risk_levels, risk_names)):
                values = [provider_data['provider_risk_summary'][p].get(risk_level, 0) for p in providers]
                fig.add_trace(
                    go.Bar(x=[p.upper() for p in providers], y=values,
                           name=f'{risk_name} Risk',
                           marker_color=self.risk_colors[risk_name],
                           showlegend=False),
                    row=1, col=2
                )

        fig.update_layout(
            title=dict(
                text="Multi-Cloud Deployment Overview",
                x=0.5,
                font=dict(size=18, family="Arial, sans-serif")
            ),
            template=self.template,
            height=600,
            showlegend=True
        )

        return fig

    def create_resource_category_sunburst(self, category_data: Dict[str, Any]) -> go.Figure:
        """Create a sunburst chart showing resource categories and providers (NEW)"""
        if not category_data:
            return self._create_empty_chart("No category data available")

        # Prepare data for sunburst chart
        ids = []
        labels = []
        parents = []
        values = []
        colors = []

        # Root
        ids.append("Total")
        labels.append("All Resources")
        parents.append("")
        values.append(0)  # Will be calculated
        colors.append("#F0F0F0")

        total_resources = 0

        # Categories
        for category, data in category_data.items():
            category_id = f"cat_{category}"
            ids.append(category_id)
            labels.append(category.title())
            parents.append("Total")
            values.append(data['count'])
            colors.append(self.provider_colors.get(category, '#666666'))
            total_resources += data['count']

        # Update total
        values[0] = total_resources

        fig = go.Figure(go.Sunburst(
            ids=ids,
            labels=labels,
            parents=parents,
            values=values,
            marker=dict(colors=colors),
            branchvalues="total",
            hovertemplate="<b>%{label}</b><br>Resources: %{value}<br><extra></extra>"
        ))

        fig.update_layout(
            title=dict(
                text="Resource Categories Breakdown",
                x=0.5,
                font=dict(size=16, family="Arial, sans-serif")
            ),
            template=self.template,
            height=500
        )

        return fig

    def create_deployment_timeline_gantt(self, timeline_data: Dict[str, Any]) -> go.Figure:
        """Create a Gantt chart for deployment timeline by provider (NEW)"""
        if not timeline_data or 'provider_specific_times' not in timeline_data:
            return self._create_empty_chart("No timeline data available")

        providers = list(timeline_data['provider_specific_times'].keys())

        # Create Gantt chart data
        df_data = []
        start_time = 0

        for i, provider in enumerate(providers):
            provider_data = timeline_data['provider_specific_times'][provider]
            # Estimate duration in minutes (rough approximation)
            duration = provider_data['resource_count'] * 2  # 2 minutes per resource

            df_data.append({
                'Provider': provider.upper(),
                'Start': start_time,
                'Finish': start_time + duration,
                'Duration': duration,
                'Resources': provider_data['resource_count']
            })

            start_time += duration * 0.3  # 30% overlap

        df = pd.DataFrame(df_data)

        fig = go.Figure()

        for i, row in df.iterrows():
            fig.add_trace(go.Bar(
                y=[row['Provider']],
                x=[row['Duration']],
                orientation='h',
                marker_color=self.provider_colors.get(row['Provider'].lower(), '#666666'),
                name=row['Provider'],
                text=f"{row['Resources']} resources",
                textposition='middle',
                hovertemplate=f"<b>{row['Provider']}</b><br>" +
                              f"Duration: {row['Duration']} min<br>" +
                              f"Resources: {row['Resources']}<br>" +
                              "<extra></extra>"
            ))

        fig.update_layout(
            title=dict(
                text="Estimated Deployment Timeline by Provider",
                x=0.5,
                font=dict(size=16, family="Arial, sans-serif")
            ),
            xaxis_title="Duration (minutes)",
            yaxis_title="Cloud Provider",
            template=self.template,
            showlegend=False,
            height=max(300, len(providers) * 80)
        )

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

        def create_multi_provider_gauge_dashboard(self, provider_risk_scores: Dict[str, float]) -> go.Figure:
            """Create multiple gauges for provider risk scores (NEW)"""
            if not provider_risk_scores:
                return self._create_empty_chart("No provider risk scores available")

            providers = list(provider_risk_scores.keys())
            num_providers = len(providers)

            # Create subplots for gauges
            if num_providers == 1:
                rows, cols = 1, 1
            elif num_providers == 2:
                rows, cols = 1, 2
            elif num_providers <= 4:
                rows, cols = 2, 2
            else:
                rows, cols = 2, 3

            fig = make_subplots(
                rows=rows, cols=cols,
                specs=[[{"type": "indicator"}] * cols for _ in range(rows)],
                subplot_titles=[f"{p.upper()} Risk" for p in providers]
            )

            for i, (provider, score) in enumerate(provider_risk_scores.items()):
                row = (i // cols) + 1
                col = (i % cols) + 1

                # Determine gauge color based on provider
                gauge_color = self.provider_colors.get(provider, '#666666')

                fig.add_trace(go.Indicator(
                    mode="gauge+number",
                    value=score,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    gauge={
                        'axis': {'range': [None, 100]},
                        'bar': {'color': gauge_color},
                        'steps': [
                            {'range': [0, 30], 'color': "lightgreen"},
                            {'range': [30, 70], 'color': "yellow"},
                            {'range': [70, 100], 'color': "lightcoral"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 2},
                            'thickness': 0.75,
                            'value': 90
                        }
                    }
                ), row=row, col=col)

            fig.update_layout(
                title=dict(
                    text="Risk Scores by Cloud Provider",
                    x=0.5,
                    font=dict(size=16, family="Arial, sans-serif")
                ),
                template=self.template,
                height=300 * rows,
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

        def create_cross_cloud_network_diagram(self, cross_provider_deps: List[Dict[str, Any]]) -> go.Figure:
            """Create a network diagram showing cross-cloud dependencies (NEW)"""
            if not cross_provider_deps:
                return self._create_empty_chart("No cross-cloud dependencies detected")

            # Create a simple network visualization
            providers = set()
            for dep in cross_provider_deps:
                providers.add(dep['primary_provider'])
                providers.extend(dep['referenced_providers'])

            providers = list(providers)

            # Create nodes
            node_x = []
            node_y = []
            node_text = []
            node_colors = []

            # Position nodes in a circle
            import math
            for i, provider in enumerate(providers):
                angle = 2 * math.pi * i / len(providers)
                node_x.append(math.cos(angle))
                node_y.append(math.sin(angle))
                node_text.append(provider.upper())
                node_colors.append(self.provider_colors.get(provider, '#666666'))

            # Create edges
            edge_x = []
            edge_y = []

            for dep in cross_provider_deps:
                primary_idx = providers.index(dep['primary_provider'])
                for ref_provider in dep['referenced_providers']:
                    if ref_provider in providers:
                        ref_idx = providers.index(ref_provider)

                        # Add edge
                        edge_x.extend([node_x[primary_idx], node_x[ref_idx], None])
                        edge_y.extend([node_y[primary_idx], node_y[ref_idx], None])

            # Create the plot
            fig = go.Figure()

            # Add edges
            fig.add_trace(go.Scatter(
                x=edge_x, y=edge_y,
                line=dict(width=2, color='#888888'),
                hoverinfo='none',
                mode='lines',
                name='Dependencies'
            ))

            # Add nodes
            fig.add_trace(go.Scatter(
                x=node_x, y=node_y,
                mode='markers+text',
                hoverinfo='text',
                text=node_text,
                textposition="middle center",
                marker=dict(
                    size=50,
                    color=node_colors,
                    line=dict(width=2, color='white')
                ),
                name='Providers'
            ))

            fig.update_layout(
                title=dict(
                    text="Cross-Cloud Dependencies",
                    x=0.5,
                    font=dict(size=16, family="Arial, sans-serif")
                ),
                template=self.template,
                showlegend=False,
                height=400,
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                margin=dict(t=50, b=50, l=50, r=50)
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

        def get_provider_color_palette(self) -> Dict[str, str]:
            """Get the provider color palette for external use (NEW)"""
            return self.provider_colors.copy()

        def create_custom_multi_cloud_chart(self, chart_type: str, data: Dict[str, Any], **kwargs) -> go.Figure:
            """Create custom charts based on chart type and data (NEW)"""
            """
            Supported chart types:
            - 'provider_comparison': Compare metrics across providers
            - 'risk_timeline': Timeline of risk changes
            - 'resource_flow': Flow of resources between states
            - 'cost_estimation': Cost estimation by provider
            """

            if chart_type == 'provider_comparison':
                return self._create_provider_comparison_chart(data, **kwargs)
            elif chart_type == 'risk_timeline':
                return self._create_risk_timeline_chart(data, **kwargs)
            elif chart_type == 'resource_flow':
                return self._create_resource_flow_chart(data, **kwargs)
            elif chart_type == 'cost_estimation':
                return self._create_cost_estimation_chart(data, **kwargs)
            else:
                return self._create_empty_chart(f"Unknown chart type: {chart_type}")

        def _create_provider_comparison_chart(self, data: Dict[str, Any], **kwargs) -> go.Figure:
            """Create a provider comparison chart"""
            # Implementation for provider comparison
            return self._create_empty_chart("Provider comparison chart - Coming soon")

        def _create_risk_timeline_chart(self, data: Dict[str, Any], **kwargs) -> go.Figure:
            """Create a risk timeline chart"""
            # Implementation for risk timeline
            return self._create_empty_chart("Risk timeline chart - Coming soon")

        def _create_resource_flow_chart(self, data: Dict[str, Any], **kwargs) -> go.Figure:
            """Create a resource flow chart"""
            # Implementation for resource flow
            return self._create_empty_chart("Resource flow chart - Coming soon")

        def _create_cost_estimation_chart(self, data: Dict[str, Any], **kwargs) -> go.Figure:
            """Create a cost estimation chart"""
            # Implementation for cost estimation
            return self._create_empty_chart("Cost estimation chart - Coming soon")

        def create_provider_confidence_chart(self, confidence_data: Dict[str, Dict[str, Any]]) -> go.Figure:
            """Create a chart showing provider detection confidence levels (NEW)"""
            if not confidence_data:
                return self._create_empty_chart("No confidence data available")

            providers = list(confidence_data.keys())
            confidence_scores = [data['score'] for data in confidence_data.values()]
            resource_counts = [data['resource_count'] for data in confidence_data.values()]

            # Create dual-axis chart
            fig = make_subplots(specs=[[{"secondary_y": True}]])

            # Confidence scores (bars)
            fig.add_trace(
                go.Bar(
                    x=[p.upper() for p in providers],
                    y=confidence_scores,
                    name="Confidence Score",
                    marker_color=[self.provider_colors.get(p, '#666666') for p in providers],
                    yaxis="y",
                    hovertemplate="<b>%{x}</b><br>Confidence: %{y:.1%}<extra></extra>"
                ),
                secondary_y=False,
            )

            # Resource counts (line)
            fig.add_trace(
                go.Scatter(
                    x=[p.upper() for p in providers],
                    y=resource_counts,
                    mode='lines+markers',
                    name="Resource Count",
                    line=dict(color='orange', width=3),
                    marker=dict(size=8),
                    yaxis="y2",
                    hovertemplate="<b>%{x}</b><br>Resources: %{y}<extra></extra>"
                ),
                secondary_y=True,
            )

            # Update layout
            fig.update_layout(
                title=dict(
                    text="Provider Detection Confidence",
                    x=0.5,
                    font=dict(size=16, family="Arial, sans-serif")
                ),
                template=self.template,
                height=400
            )

            # Update axes
            fig.update_yaxes(title_text="Confidence Score", secondary_y=False)
            fig.update_yaxes(title_text="Resource Count", secondary_y=True)

            return fig

        def create_risk_gauge_by_provider(self, provider_risk_scores: Dict[str, float]) -> go.Figure:
            """Create individual risk gauges for each provider (NEW)"""
            if not provider_risk_scores:
                return self._create_empty_chart("No provider risk scores available")

            providers = list(provider_risk_scores.keys())
            num_providers = len(providers)

            # Determine subplot layout
            if num_providers == 1:
                rows, cols = 1, 1
            elif num_providers == 2:
                rows, cols = 1, 2
            elif num_providers <= 4:
                rows, cols = 2, 2
            else:
                rows, cols = 2, 3

            # Create subplots
            fig = make_subplots(
                rows=rows, cols=cols,
                specs=[[{"type": "indicator"}] * cols for _ in range(rows)],
                subplot_titles=[f"{p.upper()}" for p in providers]
            )

            for i, (provider, score) in enumerate(provider_risk_scores.items()):
                row = (i // cols) + 1
                col = (i % cols) + 1

                fig.add_trace(go.Indicator(
                    mode="gauge+number",
                    value=score,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    gauge={
                        'axis': {'range': [None, 10]},
                        'bar': {'color': self.provider_colors.get(provider, '#666666')},
                        'steps': [
                            {'range': [0, 3], 'color': "lightgreen"},
                            {'range': [3, 7], 'color': "yellow"},
                            {'range': [7, 10], 'color': "lightcoral"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 8
                        }
                    }
                ), row=row, col=col)

            fig.update_layout(
                title=dict(
                    text="Risk Scores by Provider",
                    x=0.5,
                    font=dict(size=16, family="Arial, sans-serif")
                ),
                template=self.template,
                height=300 * rows
            )

            return fig
"""
Data Agent - Data analysis and visualization.

Capabilities:
- Analyze datasets
- Generate statistics and insights
- Create visualizations
- Data transformation and cleaning
"""

from __future__ import annotations

from src.agents.base import BaseAgent, AgentCapability, AgentContext


class DataAgent(BaseAgent):
    """Agent specialized in data analysis and visualization."""

    @property
    def name(self) -> str:
        return "data"

    @property
    def description(self) -> str:
        return "Analyzes data, generates insights, and creates visualizations."

    @property
    def capabilities(self) -> list[AgentCapability]:
        return [AgentCapability.DATA]

    def get_allowed_tools(self) -> list[str]:
        return ["bash", "read_file", "write_file", "list_dir"]

    def get_system_prompt(self, context: AgentContext) -> str:
        return f"""You are a Data Agent - an expert in data analysis and visualization.

## Your Role
You analyze data and extract meaningful insights:
- Statistical analysis
- Data cleaning and transformation
- Visualization generation
- Pattern recognition
- Report generation

## Analysis Workflow
1. **Understand**: Clarify what insights are needed
2. **Explore**: Examine data structure and quality
3. **Clean**: Handle missing values, outliers, inconsistencies
4. **Analyze**: Apply appropriate statistical methods
5. **Visualize**: Create clear, informative charts
6. **Report**: Summarize findings with actionable insights

## Available Tools
- `bash`: Run Python/pandas scripts for analysis
- `read_file`: Load data files (CSV, JSON, etc.)
- `write_file`: Save results and reports
- `list_dir`: Browse data directories

## Python Libraries
Use these for analysis (ensure they're installed):
- pandas: Data manipulation
- numpy: Numerical operations
- matplotlib/seaborn: Visualization
- scipy: Statistical tests

## Code Templates
For quick analysis, use:
```python
import pandas as pd
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv('data.csv')

# Basic stats
print(df.describe())

# Visualization
df.plot(kind='bar')
plt.savefig('chart.png')
```

## Current Task
{context.task}

## Workspace
Working directory: {context.workspace_path or 'current directory'}

Analyze the data thoroughly and provide actionable insights."""

    def can_handle(self, task: str) -> float:
        """Score how well this agent can handle the task."""
        keywords = [
            "analyze", "data", "statistics", "chart", "graph", "plot",
            "visualization", "csv", "excel", "dataset", "metrics",
            "insights", "trends", "correlation", "report",
        ]
        task_lower = task.lower()
        matches = sum(1 for kw in keywords if kw in task_lower)
        return min(0.2 + (matches * 0.18), 0.95)

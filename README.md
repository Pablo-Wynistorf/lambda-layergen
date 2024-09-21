# Lambda Layer Generator

This application helps you generate AWS Lambda layers with ease. It simplifies the process of packaging and deploying dependencies for your Lambda functions.

## Installation

To install and run the Lambda Layer Generator, execute the following command in your terminal:

```bash
curl -sSL https://raw.githubusercontent.com/Pablo-Wynistorf/lambda-layergen/main/install.sh | bash
```

## Prerequisites

Before using this application, ensure you have the following tools installed:

- **AWS CLI**: To upload the layers to your aws account
- **npm**: To install the npm dependencies
- **pip**: To install the pip dependencies

## Commands

The Lambda Layer Generator offers the following commands:

- `layergen list`: List all layers in selected region.
- `layergen create`: Create new layer for node or python functions
- `layergen delete`: Delete layerversion in selected region
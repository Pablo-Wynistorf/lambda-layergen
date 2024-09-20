import os
import shutil
import subprocess
import tempfile

import click


# Helper functions
def check_dependencies():
    """Check if AWS CLI, pip, and npm are installed."""
    has_dependencies = True

    if shutil.which("aws") is None:
        has_dependencies = False

    if shutil.which("pip") is None:
        has_dependencies = False

    if shutil.which("npm") is None:
        has_dependencies = False

    if not has_dependencies:
        click.echo(
            "Please install the AWS CLI, pip, and npm before running this script."
        )
        return


def check_aws_signed_in():
    """Check if the user is signed in to AWS CLI."""
    try:
        subprocess.run(
            ["aws", "sts", "get-caller-identity"], check=True, capture_output=True
        )
    except subprocess.CalledProcessError:
        click.echo("Please sign in to the AWS CLI before running this script.")
        return


def get_default_region():
    """Get the default AWS region from the AWS CLI configuration."""
    result = subprocess.run(
        ["aws", "configure", "get", "region"],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else None


# Main CLI Group
@click.group()
def cli():
    """A CLI tool to manage AWS Lambda Layers."""
    pass


# Create command
@cli.command()
@click.option(
    "--layer-name",
    prompt="Enter the AWS Lambda Layer name",
    help="The name of the AWS Lambda Layer.",
)
@click.option(
    "--runtime",
    type=click.Choice(["nodejs", "python"], case_sensitive=False),
    prompt="Select the runtime",
    help="The runtime environment for the Lambda Layer.",
)
@click.option(
    "--packages",
    prompt="Enter the packages you want to include (space-separated)",
    help="Packages to include in the Lambda Layer.",
)
@click.option(
    "--region",
    help="AWS region to upload the Lambda Layer to (default: AWS configured region).",
)
def create(layer_name, runtime, packages, region):
    """Create and upload an AWS Lambda Layer."""
    check_dependencies()
    check_aws_signed_in()

    if runtime == "nodejs":
        click.echo("You selected Node.js 20.x")
        runtime_version = "nodejs20.x"
        runtime_dir = "nodejs"
    elif runtime == "python":
        click.echo("You selected Python 3.12")
        runtime_version = "python3.12"
        runtime_dir = "python"

    # Use the configured region if not provided
    if region is None:
        region = get_default_region()

    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        os.makedirs(f"{temp_dir}/{runtime_dir}", exist_ok=True)

        try:
            if runtime == "nodejs":
                os.makedirs(f"{temp_dir}/{runtime_dir}/node_modules", exist_ok=True)
                subprocess.run(
                    ["npm", "install", "--prefix", f"{temp_dir}/{runtime_dir}"]
                    + packages.split(),
                    check=True,
                )
            else:
                subprocess.run(
                    ["pip", "install", "--target", f"{temp_dir}/{runtime_dir}"]
                    + packages.split(),
                    check=True,
                )

            # Create the zip file
            zip_file = f"{layer_name}.zip"
            shutil.make_archive(layer_name, "zip", temp_dir)

            if not os.path.exists(zip_file):
                click.echo("Zip file was not created.")
                return

            subprocess.run(
                [
                    "aws",
                    "lambda",
                    "publish-layer-version",
                    "--layer-name",
                    layer_name,
                    "--zip-file",
                    f"fileb://{zip_file}",
                    "--compatible-runtimes",
                    runtime_version,
                    "--region",
                    region,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )

            os.remove(zip_file)
            click.echo(
                f"Layer {layer_name} has been successfully created and uploaded to AWS Lambda!"
            )
        except subprocess.CalledProcessError as e:
            click.echo(f"Error: {e}")
            return


# List command
@cli.command()
@click.option(
    "--region",
    help="AWS region to list Lambda layers from (default: AWS configured region).",
)
def list(region):
    """List all AWS Lambda Layers."""
    check_dependencies()
    check_aws_signed_in()

    # Use the configured region if not provided
    if region is None:
        region = get_default_region()

    if region is None:
        click.echo(
            "Error: No AWS region specified. Please set AWS_DEFAULT_REGION or configure your AWS CLI."
        )
        return

    result = subprocess.run(
        ["aws", "lambda", "list-layers", "--region", region],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        click.echo("Error listing layers.")
    else:
        click.echo(result.stdout)


# Delete command
@cli.command()
@click.option(
    "--layer-name",
    prompt="Enter the AWS Lambda Layer name",
    help="The name of the AWS Lambda Layer to delete.",
)
@click.option(
    "--version-number",
    prompt="Enter the version number to delete",
    help="The version number of the layer to delete.",
)
@click.option(
    "--region",
    help="AWS region to delete the Lambda Layer from (default: AWS configured region).",
)
def delete(layer_name, version_number, region):
    """Delete an AWS Lambda Layer."""
    check_dependencies()
    check_aws_signed_in()

    # Use the configured region if not provided
    if region is None:
        region = get_default_region()

    if region is None:
        click.echo(
            "Error: No AWS region specified. Please set AWS_DEFAULT_REGION or configure your AWS CLI."
        )
        return

    try:
        subprocess.run(
            [
                "aws",
                "lambda",
                "delete-layer-version",
                "--layer-name",
                layer_name,
                "--version-number",
                version_number,
                "--region",
                region,
            ],
            check=True,
        )
        click.echo(f"Layer {layer_name} version {version_number} has been deleted.")
    except subprocess.CalledProcessError:
        click.echo("Error deleting the layer.")
        return


# Entry point
if __name__ == "__main__":
    cli()

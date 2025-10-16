"""
Master Pipeline Runner
======================
This script runs the complete data pipeline:
Bronze → Silver → Gold

Usage:
    python scripts/run_pipeline.py [--layer LAYER]

Arguments:
    --layer: Run specific layer only (bronze, silver, gold, or all)
             Default: all

Examples:
    python scripts/run_pipeline.py              # Run all layers
    python scripts/run_pipeline.py --layer bronze
    python scripts/run_pipeline.py --layer silver
"""

import sys
import os
import subprocess
from datetime import datetime
import argparse


def print_header(message):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {message}")
    print("=" * 80 + "\n")


def run_script(script_path, layer_name):
    """
    Run a Python script and capture output
    
    Args:
        script_path: Path to the script
        layer_name: Name of the layer (for logging)
        
    Returns:
        True if successful, False otherwise
    """
    print_header(f"Running {layer_name.upper()} Layer")
    print(f"Script: {script_path}")
    print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        # Run the script using Python
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=False,  # Show output in real-time
            text=True,
            check=True
        )
        
        print(f"\n✅ {layer_name.upper()} layer completed successfully")
        print(f"End: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {layer_name.upper()} layer failed")
        print(f"Error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error in {layer_name.upper()} layer")
        print(f"Error: {e}")
        return False


def run_bronze_layer():
    """Run Bronze layer (raw load)"""
    return run_script("scripts/bronze/raw_load.py", "Bronze")


def run_silver_layer():
    """Run Silver layer (parse and transform)"""
    return run_script("scripts/silver/silver_load.py", "Silver")


def run_gold_layer():
    """Run Gold layer (final curated)"""
    return run_script("scripts/gold/gold_load.py", "Gold")


def main():
    """Main execution"""
    
    parser = argparse.ArgumentParser(description="Run OpenSSH Log Pipeline")
    parser.add_argument(
        '--layer',
        choices=['bronze', 'silver', 'gold', 'all'],
        default='all',
        help='Which layer to run (default: all)'
    )
    
    args = parser.parse_args()
    
    print("\n" + "█" * 80)
    print("█" + " " * 78 + "█")
    print("█" + "  OpenSSH Log Processing Pipeline".center(78) + "█")
    print("█" + "  Bronze → Silver → Gold".center(78) + "█")
    print("█" + " " * 78 + "█")
    print("█" * 80)
    
    start_time = datetime.now()
    print(f"\nPipeline started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = True
    layers_to_run = []
    
    # Determine which layers to run
    if args.layer == 'all':
        layers_to_run = ['bronze', 'silver', 'gold']
    else:
        layers_to_run = [args.layer]
    
    print(f"Layers to run: {', '.join(layers_to_run).upper()}\n")
    
    # Run layers in sequence
    for layer in layers_to_run:
        if layer == 'bronze':
            success = run_bronze_layer()
        elif layer == 'silver':
            if success or args.layer == 'silver':
                success = run_silver_layer()
            else:
                print("⚠️ Skipping Silver layer due to Bronze layer failure")
        elif layer == 'gold':
            if success or args.layer == 'gold':
                success = run_gold_layer()
            else:
                print("⚠️ Skipping Gold layer due to previous layer failure")
        
        if not success and args.layer == 'all':
            print("\n❌ Pipeline stopped due to layer failure")
            break
    
    # Summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("\n" + "=" * 80)
    print("  PIPELINE SUMMARY")
    print("=" * 80)
    print(f"Start Time:    {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"End Time:      {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duration:      {duration}")
    print(f"Status:        {'✅ SUCCESS' if success else '❌ FAILED'}")
    print("=" * 80)
    
    if success:
        print("\n🎉 Pipeline completed successfully!")
        print("\nOutput locations:")
        print("  📁 Bronze: data/bronze/raw_logs.parquet")
        print("  📁 Silver: data/silver/structured_logs.json")
        print("  📁 Gold:   data/gold/openssh_logs_final.csv")
        print("\n")
    else:
        print("\n⚠️ Pipeline completed with errors. Check logs above for details.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""
MAG16 Complete Migration Script

Master orchestration script that runs the complete MAG16 migration process:
1. Portfolio setup
2. Asset migration 
3. Concentration threshold extraction
4. Waterfall/scenario configuration
5. Testing and validation

This script provides a single entry point for full MAG16 migration.
"""

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

class MAG16MasterMigrator:
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.migration_scripts = [
            ("setup_mag16_portfolio.py", "Portfolio & Database Setup"),
            ("extract_mag16_assets.py", "Asset Migration (235 assets)"),
            ("extract_mag16_thresholds.py", "Concentration Threshold Extraction"),
            ("extract_mag16_waterfall.py", "Waterfall & Scenario Configuration"),
            ("test_mag16_migration.py", "Testing & Validation")
        ]
        
    def run_complete_migration(self):
        """Run complete MAG16 migration process"""
        print("🚀 MAG16 Complete Migration")
        print("=" * 70)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Scripts Directory: {self.script_dir}")
        print()
        
        results = []
        
        try:
            for i, (script_name, description) in enumerate(self.migration_scripts, 1):
                print(f"📋 Step {i}/{len(self.migration_scripts)}: {description}")
                print(f"    Running: {script_name}")
                print("-" * 50)
                
                result = self._run_script(script_name)
                results.append({
                    "step": i,
                    "script": script_name,
                    "description": description,
                    "success": result["success"],
                    "duration": result["duration"],
                    "output": result["output"]
                })
                
                if result["success"]:
                    print(f"    ✅ Step {i} completed successfully ({result['duration']:.1f}s)")
                else:
                    print(f"    ❌ Step {i} failed ({result['duration']:.1f}s)")
                    print(f"    Error: {result['output'][-500:]}")  # Last 500 chars
                    
                    # Ask user whether to continue
                    if i < len(self.migration_scripts):
                        response = input(f"\n    Continue with remaining steps? (y/N): ")
                        if response.lower() != 'y':
                            print("    Migration stopped by user")
                            break
                
                print()
            
            # Generate final summary
            self._generate_migration_summary(results)
            
        except KeyboardInterrupt:
            print("\n⚠️  Migration interrupted by user")
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            raise
    
    def _run_script(self, script_name: str) -> dict:
        """Run a migration script and capture results"""
        script_path = self.script_dir / script_name
        
        if not script_path.exists():
            return {
                "success": False,
                "duration": 0,
                "output": f"Script not found: {script_path}"
            }
        
        start_time = datetime.now()
        
        try:
            # Run the script as a subprocess
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            return {
                "success": result.returncode == 0,
                "duration": duration,
                "output": result.stdout + result.stderr
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "duration": 300,
                "output": "Script execution timed out after 5 minutes"
            }
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            return {
                "success": False,
                "duration": duration,
                "output": f"Script execution error: {e}"
            }
    
    def _generate_migration_summary(self, results: list):
        """Generate final migration summary"""
        print("📊 MIGRATION SUMMARY")
        print("=" * 70)
        
        successful_steps = sum(1 for result in results if result["success"])
        total_steps = len(results)
        total_duration = sum(result["duration"] for result in results)
        
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total Duration: {total_duration:.1f} seconds ({total_duration/60:.1f} minutes)")
        print(f"Steps Completed: {successful_steps}/{total_steps}")
        print()
        
        # Step-by-step results
        print("Step Results:")
        for result in results:
            status = "✅" if result["success"] else "❌"
            print(f"  {status} Step {result['step']}: {result['description']} ({result['duration']:.1f}s)")
        
        # Overall status
        print()
        if successful_steps == total_steps:
            print("🎉 MAG16 MIGRATION COMPLETE!")
            print("   All steps completed successfully")
            print("   MAG16 is ready for production use")
            print()
            print("Next Steps:")
            print("  • Access MAG16 via frontend: Portfolio MAG16-001")
            print("  • Review concentration test results")
            print("  • Verify asset data integrity")
            print("  • Test waterfall calculations")
        elif successful_steps >= total_steps - 1:
            print("⚠️  MAG16 MIGRATION MOSTLY COMPLETE")
            print("   Minor issues detected, but system should be functional")
            print("   Review failed steps and resolve before production")
        else:
            print("❌ MAG16 MIGRATION INCOMPLETE")
            print("   Significant issues detected")
            print("   Review failed steps and re-run migration")
        
        # Save detailed log
        log_file = self.script_dir / f"mag16_migration_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(log_file, 'w') as f:
            f.write("MAG16 Migration Log\\n")
            f.write("=" * 50 + "\\n")
            f.write(f"Date: {datetime.now()}\\n")
            f.write(f"Success Rate: {successful_steps}/{total_steps}\\n")
            f.write(f"Total Duration: {total_duration:.1f}s\\n\\n")
            
            for result in results:
                f.write(f"Step {result['step']}: {result['description']}\\n")
                f.write(f"Script: {result['script']}\\n")
                f.write(f"Success: {result['success']}\\n")
                f.write(f"Duration: {result['duration']:.1f}s\\n")
                f.write("Output:\\n")
                f.write(result['output'])
                f.write("\\n" + "=" * 50 + "\\n\\n")
        
        print(f"\\n📄 Detailed log saved: {log_file}")

def main():
    """Main migration orchestration"""
    print("MAG16 Complete Migration System")
    print("This will run the full MAG16 migration process:")
    print("  • Portfolio setup")
    print("  • Asset migration (235 assets)")  
    print("  • Concentration threshold extraction")
    print("  • Waterfall configuration")
    print("  • Testing & validation")
    print()
    
    # Check prerequisites
    excel_file = Path(__file__).parent.parent.parent / "TradeHypoPrelimv32.xlsm"
    if not excel_file.exists():
        print(f"❌ Excel file not found: {excel_file}")
        print("Please ensure TradeHypoPrelimv32.xlsm is in the project root")
        return
    
    print(f"✅ Excel file found: {excel_file}")
    print()
    
    response = input("Proceed with MAG16 migration? (y/N): ")
    if response.lower() != 'y':
        print("Migration cancelled")
        return
    
    try:
        migrator = MAG16MasterMigrator()
        migrator.run_complete_migration()
        
    except Exception as e:
        print(f"\\n❌ MAG16 Complete Migration Failed: {e}")
        raise

if __name__ == "__main__":
    main()
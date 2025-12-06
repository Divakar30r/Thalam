# Python Compilation Script for gRPC Proto Files

import subprocess
import sys
import os
from pathlib import Path

def compile_proto_files():
    """Compile protocol buffer files to Python code"""
    
    # Get project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Set paths
    proto_dir = project_root / "shared" / "proto"
    output_dir = project_root / "shared" / "proto" / "generated"
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    # Find all .proto files
    proto_files = list(proto_dir.glob("*.proto"))
    
    if not proto_files:
        print("No .proto files found in", proto_dir)
        return False
    
    print(f"Found {len(proto_files)} proto files to compile:")
    for proto_file in proto_files:
        print(f"  - {proto_file.name}")
    
    # Compile each proto file
    for proto_file in proto_files:
        try:
            cmd = [
                sys.executable, "-m", "grpc_tools.protoc",
                f"--proto_path={proto_dir}",
                f"--python_out={output_dir}",
                f"--grpc_python_out={output_dir}",
                str(proto_file)
            ]
            
            print(f"\nCompiling {proto_file.name}...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✓ Successfully compiled {proto_file.name}")
            else:
                print(f"✗ Failed to compile {proto_file.name}")
                print(f"Error: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"✗ Exception compiling {proto_file.name}: {str(e)}")
            return False
    
    # Create __init__.py in generated directory
    init_file = output_dir / "__init__.py"
    if not init_file.exists():
        with open(init_file, "w") as f:
            f.write('# Generated protocol buffer files\n\n__version__ = "1.0.0"\n')
        print(f"✓ Created {init_file}")
    
    print(f"\n🎉 Protocol buffer compilation completed!")
    print(f"Generated files in: {output_dir}")
    
    # List generated files
    generated_files = list(output_dir.glob("*.py"))
    for file in generated_files:
        print(f"  - {file.name}")
    
    return True

if __name__ == "__main__":
    try:
        success = compile_proto_files()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Compilation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)
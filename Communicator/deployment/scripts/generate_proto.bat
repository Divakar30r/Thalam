@echo off
REM Protocol Buffer Compilation Script for Windows

REM Set paths
set PROTO_DIR=..\..\shared\proto
set OUTPUT_DIR=..\..\shared\proto\generated

REM Create output directory if it doesn't exist
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

REM Compile protocol buffers
python -m grpc_tools.protoc --proto_path="%PROTO_DIR%" --python_out="%OUTPUT_DIR%" --grpc_python_out="%OUTPUT_DIR%" "%PROTO_DIR%\order_service.proto"

REM Create __init__.py in generated directory
echo. > "%OUTPUT_DIR%\__init__.py"

echo Protocol buffer compilation completed!
echo Generated files:
dir "%OUTPUT_DIR%"
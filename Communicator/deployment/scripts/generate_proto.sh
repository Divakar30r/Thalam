#!/bin/bash
# Protocol Buffer Compilation Script

# Set paths
PROTO_DIR="../shared/proto"
OUTPUT_DIR="../shared/proto/generated"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Compile protocol buffers
python -m grpc_tools.protoc \
    --proto_path="$PROTO_DIR" \
    --python_out="$OUTPUT_DIR" \
    --grpc_python_out="$OUTPUT_DIR" \
    "$PROTO_DIR/order_service.proto"

# Create __init__.py in generated directory
touch "$OUTPUT_DIR/__init__.py"

echo "Protocol buffer compilation completed!"
echo "Generated files:"
ls -la "$OUTPUT_DIR"
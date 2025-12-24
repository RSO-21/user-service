# app/grpc/orders_client.py
import os
import grpc
from . import orders_pb2, orders_pb2_grpc

ORDERS_GRPC_HOST = os.getenv("ORDERS_GRPC_HOST", "orders-ms")
ORDERS_GRPC_PORT = int(os.getenv("ORDERS_GRPC_PORT", "50051"))

def get_orders_by_user(user_id: int, tenant_id: str | None = None, timeout_s: float = 2.0):
    target = f"{ORDERS_GRPC_HOST}:{ORDERS_GRPC_PORT}"

    # insecure for in-cluster demo; in production use mTLS/mesh
    with grpc.insecure_channel(target) as channel:
        stub = orders_pb2_grpc.OrdersServiceStub(channel)

        metadata = []
        if tenant_id:
            metadata.append(("x-tenant-id", tenant_id))

        return stub.GetOrdersByUser(
            orders_pb2.GetOrdersByUserRequest(user_id=user_id),
            timeout=timeout_s,
            metadata=metadata,
        )

import asyncio
import sys
import time
from aioquic.asyncio import connect, QuicConnectionProtocol
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import StreamDataReceived

BUF_SIZE = 65536
ONE_GB = 1073741824
FIVE_HUNDRED_MB = 524288000

class QuicClientProtocol(QuicConnectionProtocol):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ack_futures = {}

    def quic_event_received(self, event):
        if isinstance(event, StreamDataReceived):
            if event.data == b"ACK":
                fut = self.ack_futures.get(event.stream_id)
                if fut and not fut.done():
                    fut.set_result(True)

async def run_quic_client(server, port, block_size, total_bytes, mode='st'):
    configuration = QuicConfiguration(is_client=True)
    configuration.verify_mode = False
    bytes_sent = 0
    total_messages = 0
    start_time = time.time()
    
    if mode == 'sw':
        async with connect(server, port, configuration=configuration, create_protocol=QuicClientProtocol) as client:
            while bytes_sent < total_bytes:
                stream_id = client._quic.get_next_available_stream_id()
                to_send = min(block_size, total_bytes - bytes_sent)
                ack_future = asyncio.get_running_loop().create_future()
                client.ack_futures[stream_id] = ack_future
                client._quic.send_stream_data(stream_id, bytes(to_send), True)
                client.transmit()
                
                try:
                    await asyncio.wait_for(ack_future, timeout=2.0)
                except asyncio.TimeoutError:
                    print("ERROR receiving ACK")
                    sys.exit(1)
                bytes_sent += to_send
                total_messages += 1
    else:
        async with connect(server, port, configuration=configuration) as client:
            stream_id = client._quic.get_next_available_stream_id()
            while bytes_sent < total_bytes:
                to_send = min(block_size, total_bytes - bytes_sent)
                client._quic.send_stream_data(stream_id, bytes(to_send), False)
                client.transmit()
                bytes_sent += to_send
                total_messages += 1
                await asyncio.sleep(0)
            
            # await asyncio.sleep(60)
            client._quic.send_stream_data(stream_id, b'', True)
            client.transmit()
        
    end_time = time.time()
    elapsed = end_time - start_time
    print("Protocol used: QUIC")
    if mode == 'sw':
        print("Mode used: Stop and Wait")
    else:
        print("Mode used: Streaming")
    print(f"Total transmission time: {elapsed:.6f} seconds")
    print("Total number of messages sent:", total_messages)
    print("Total number of bytes sent:", bytes_sent)
        
    await asyncio.sleep(1)

def main():
    if len(sys.argv) < 4:
        print(f"Usage: {sys.argv[0]} <mode> <server_ip> <block_size> <total_bytes_to_send>")
        print("  mode: streaming (use: st) or stopandwait (use: sw) (default: streaming)")
        print(f"  block_size: size of each message (1 to {BUF_SIZE})")
        print(f"  total_bytes_to_send: total number of bytes to send (1GB or 500MB)")
        sys.exit(1)
    if len(sys.argv) == 4:
        mode = 'st'
        server = sys.argv[1]
        block_size = int(sys.argv[2])
        total_bytes = ONE_GB if sys.argv[3] == '1GB' else FIVE_HUNDRED_MB
    else:
        mode = sys.argv[1]
        server = sys.argv[2]
        block_size = int(sys.argv[3])
        total_bytes = ONE_GB if sys.argv[4] == '1GB' else FIVE_HUNDRED_MB
        
    if mode not in ['st', 'sw']:
        print("Invalid mode")
        sys.exit(1)
    
    port = 5001    
    asyncio.run(run_quic_client(server, port, block_size, total_bytes, mode))

if __name__ == "__main__":
    main()

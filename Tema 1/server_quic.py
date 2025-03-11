import asyncio
import sys
from aioquic.asyncio import QuicConnectionProtocol, serve
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import StreamDataReceived, ConnectionTerminated

BUF_SIZE = 65536

class QuicServerProtocol(QuicConnectionProtocol):
    def __init__(self, *args, mode='st', **kwargs):
        super().__init__(*args, **kwargs)
        self.total_bytes = 0
        self.total_messages = 0
        self.mode = mode
        self.ack_sent = {}

    def quic_event_received(self, event):
        if isinstance(event, StreamDataReceived):
            stream_id = event.stream_id
            self.total_bytes += len(event.data)
            self.total_messages += 1

            if self.mode == 'sw':
                if event.end_stream and stream_id not in self.ack_sent:
                    ack = b"ACK"
                    self._quic.send_stream_data(stream_id, ack, end_stream=True)
                    self.ack_sent[stream_id] = True

        if isinstance(event, ConnectionTerminated):
            print("Protocol used: QUIC")
            print(f"Mode used: {'Stop and Wait' if self.mode == 'sw' else 'Streaming'}")
            print("Total messages received:", self.total_messages)
            print("Total bytes received:", self.total_bytes)
            sys.exit(0)
            

async def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <mode> <certificate> <private_key>")
        print("  mode: streaming (use: st) or stopandwait (use: sw) (default: streaming)")
        sys.exit(1)
    if len(sys.argv) == 3:
        mode = 'st'
        cert_file = sys.argv[1]
        key_file = sys.argv[2]
    else:
        mode = sys.argv[1]
        cert_file = sys.argv[2]
        key_file = sys.argv[3]
    
    if mode not in ['st', 'sw']:
        print("Invalid mode")
        sys.exit(1)
        
    port = 5001
    
    configuration = QuicConfiguration(is_client=False)
    configuration.load_cert_chain(cert_file, key_file)
    
    await serve(
        host="0.0.0.0",
        port=port,
        configuration=configuration,
        create_protocol=lambda *args, **kwargs: QuicServerProtocol(*args, mode=mode, **kwargs),
    )
    print(f"QUIC server listening on port {port}...")
    
    await asyncio.get_event_loop().create_future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

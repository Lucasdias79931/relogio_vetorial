import grpc
import threading
from enum import Enum
import os
import Talk_pb2, Talk_pb2_grpc
import time
from concurrent import futures
import random


class TypeEvent(Enum):
    Local_event = 0
    Sent_message = 1
    Receive_message = 2 

    

class Utils:
    def __init__(self):
        pass

    @staticmethod
    def update_data_clock_in_log(id_local_process, type_event, clock, data_clock_path):
        try:
            with open(data_clock_path, 'a') as file:
                file.write(f"p[{id_local_process}] > {type_event.name} > {clock}\n")
        except FileNotFoundError as e:
            raise e
    @staticmethod    
    def updateClock_vector( local_clock, id_local_process,received_clock):
        """
        Update the vector clock of this process based on the received vector.
        """
        try:
            
            for i in range(len(local_clock)):
                local_clock[i] = max(local_clock[i], received_clock[i])
            
            local_clock[id_local_process] += 1
           
        except Exception as e:
            raise ValueError(f"Error updating the clock: {e}")
        

class TalkServer(Talk_pb2_grpc.SpeakxServiceServicer):
    """
        This class received a greet from a client and a vetorial clock
        As response, this, push a 'hello, i received your greeting'
    """
    def __init__(self, data_clock_path, server_clock, id_server_clock):
        self.data_clock_path = data_clock_path
        self.local_clock = server_clock
        self.id_server_clock = id_server_clock
        self.utils = Utils()
        self._lock = threading.Lock()
        super().__init__()

    def Talk(self, request, context):
        try:
            # data received from client
            speak = request.speak
            received_clock = list(request.vectorClock)
            peer = context.peer()
        
            print(f"Message received from {peer}: '{speak}'")
            print(f"Clock from {peer}: {received_clock}")

            with self._lock:
                # update server clock
                self.utils.updateClock_vector(self.local_clock, self.id_server_clock, received_clock)

                # save server clock
                self.utils.update_data_clock_in_log(
                    id_local_process=self.id_server_clock,
                    type_event=TypeEvent.Receive_message,
                    clock=self.local_clock,
                    data_clock_path=self.data_clock_path
                )

            print(f"server clock updated: {self.local_clock}")

            # assembly response 
            response = Talk_pb2.ResponseGreeting(
                speak=f"hello, i received your greeting: {speak}",
                vectorClock=self.local_clock
            )


            with self._lock:
                # update server clock
                self.local_clock[self.id_server_clock] += 1

                # save server clock
                self.utils.update_data_clock_in_log(
                    id_local_process=self.id_server_clock,
                    type_event=TypeEvent.Sent_message,
                    clock=self.local_clock,
                    data_clock_path=self.data_clock_path
                )


            return response

        except FileNotFoundError as e:
            context.abort(grpc.StatusCode.NOT_FOUND, f"File Not Found: {e}")
        except ValueError as e:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(e))
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, f"Unexpected error: {e}")

   
  
class TalkClient():
    def __init__(self,data_clock_path, client_clock, id_client_process,host="localhost", port=5051):
        self.host = host
        self.port = port
        self.data_clock_path = data_clock_path
        self.client_clock = client_clock
        self.id_client_process = id_client_process
        self.utils = Utils()
        self._lock = threading.Lock()
        channel = grpc.insecure_channel(f'{host}:{port}')
        self.stub = Talk_pb2_grpc.SpeakxServiceStub(channel)



    def send_greeting(self, speak):
        try:
            with self._lock:
                self.client_clock[self.id_client_process] += 1
                Utils.update_data_clock_in_log(
                    id_local_process = self.id_client_process,
                    type_event = TypeEvent.Sent_message,
                    clock = self.client_clock,
                    data_clock_path  = self.data_clock_path)
            # assemble request
            request = Talk_pb2.Greeting(
                speak=speak,
                vectorClock=self.client_clock
            )

            response =  self.stub.Talk(request)

            with self._lock:
                Utils.updateClock_vector(
                    local_clock = self.client_clock,
                    id_local_process = self.id_client_process,
                    received_clock = list(response.vectorClock)
                )

                Utils.update_data_clock_in_log(
                    id_local_process = self.id_client_process,
                    type_event = TypeEvent.Receive_message,
                    clock = self.client_clock,
                    data_clock_path  = self.data_clock_path)
            
            return response.speak, list(response.vectorClock)
        except grpc.RpcError as e:
            print(f"RPC failed: {e.code()} - {e.details()}")
        except Exception as e:
            print(f"Unexpected error: {e}")




def eventCliente(host, ports, data_clock_path, client_clock, id_client_process):
    lock = threading.Lock()
    

    start = time.time()

    while time.time() - start < 120:
        port_idx = 0

        while port_idx == id_client_process:
            port_idx = random.randint(0,len(ports)-1)
        client = TalkClient(
            data_clock_path=data_clock_path,
            client_clock=client_clock,
            id_client_process=id_client_process,
            host=host,
            port=ports[port_idx]
        )
        with lock:
             Utils.update_data_clock_in_log(
                id_local_process = id_client_process,
                type_event= TypeEvent.Local_event,
                clock = client_clock,
                data_clock_path = data_clock_path)


        time.sleep(3)


        soma = 2 + 3
        client_clock[id_client_process] += 1

        with lock:
            Utils.update_data_clock_in_log(
                id_local_process = id_client_process,
                type_event= TypeEvent.Local_event,
                clock = client_clock,
                data_clock_path = data_clock_path)

        time.sleep(5)

        client.send_greeting(f"hello")


def Server(host, port, data_clock_path, server_clock, id_server_clock):
    """

    Args:
        host (str): Host address to bind the server (e.g., 'localhost').
        port (int): Port number to listen for connections.
        data_clock_path (str): Path to save clock updates.
        server_clock (list[int]): Reference to the server's vector clock.
        id_server_clock (int): ID of this server in the vector clock.
    """
    try:
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))


        # Register the service implementation
        servicer = TalkServer(data_clock_path, server_clock, id_server_clock)
        Talk_pb2_grpc.add_SpeakxServiceServicer_to_server(servicer, server)

        # Bind server to the given host and port
        address = f"{host}:{port}"
        server.add_insecure_port(address)

        print(f"Server started at {address}")
        print(f"Initial vector clock: {server_clock}")

        server.start()
        print("Server is running. Press Ctrl+C to stop.")
        server.wait_for_termination()

    except KeyboardInterrupt:
        print("\nServer stopped by user.")
    except Exception as e:
        print(f"Unexpected error while running server: {e}")



if __name__ == "__main__":
    process = [[0,0,0,0] for _ in range(4)]

    log_base = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'log_clock')
    os.makedirs(log_base, exist_ok=True)

    full_path_log = [os.path.join(log_base, f'process_{i}.txt') for i in range(1, len(process) + 1)]
    ports = list(range(5051, 5051 + len(process)))
    for idx in range(len(process)):

        t = threading.Thread(
            target=Server,
            kwargs={
                "host": "localhost",
                "port": ports[idx],
                "data_clock_path": full_path_log[idx],
                "server_clock": process[idx],
                "id_server_clock": idx
            },
            daemon=True
        )
       
        t.start()

    time.sleep(2)

    ports = list(range(5051, 5051 + len(process)))
    allThreads = []

    for idx in range(len(process)):
        t = threading.Thread(
            target=eventCliente,
            kwargs={
                "host": "localhost",
                "ports" :ports,
                "data_clock_path" :full_path_log[idx],
                "id_client_process" : idx,
                "client_clock" : process[idx]
            },
            daemon=True
        )
        allThreads.append(t)
        t.start()

    
    for _t in allThreads:
        _t.join()
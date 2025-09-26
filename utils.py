import os
import traceback
from enum import Enum

class TypeEvent(Enum):
    Local_event = 0
    Sent_message = 1
    Receive_message = 2 

class Utils:
    def __init__(self):
        pass


    """
        This function can be used to register log about a process
    """
    @staticmethod
    def register(id_process:str, N_action:dict, path_log:str, type_event: TypeEvent, external_process:int)->None:
        try:
            with open(path_log, 'a') as file:
                if type_event == 0:
                    
                    file.write(f'[{id_process}] Local event > {N_action}')

                elif type_event == 1:
                    if not external_process:
                        raise ValueError("not foud the number of external process")
                    file.write(f'[{id_process}] sent menssage to {external_process} > {N_action}')
                else:
                    if not external_process:
                        raise ValueError("not foud the number of external process")
                    file.write(f'[{id_process}] Receive menssage from {external_process} > {N_action}')
        except Exception as e:
            tb = traceback.format_exc()
            raise ValueError(f"Error in register: {e}\nTraceback:\n{tb}")
        

    @staticmethod
    def increment_NAction(N_action: dict, id_process):
        try:
            if id_process not in N_action:
                raise ValueError(f"The process [{id_process}] isn't in N_action")

            N_action[id_process] += 1

        except Exception as e:
            tb = traceback.format_exc()
            raise ValueError(f"Error incrementing N_action: {e}\nTraceback:\n{tb}")

    

if __name__ == "__main__":
    
    id_process = 'p1'
    # The process id
    N_action = {'p1':0, 'p2':0,'p3':0,'p4':0}
    # This dict represent four process and your respective events.

    path_log = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'log/')
    os.makedirs(path_log)
    path_log = os.path.join(path_log,f'process_{id_process}.txt' )

    Utils.register(id_process= id_process,N_action=N_action, path_log=path_log)
   

    
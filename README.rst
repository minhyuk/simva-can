Python CAN Interface for SimVA
==================================

Creates a Python-CAN interface using dual UDP(send, recv) bridge which provide by SimVA product.
Here is example, mixed with python-remote-can_

.. code-block::

    bus = can.Bus(interface='remote', channel='ws://localhost:54701', bitrate=50000, receive_own_messages=True)
    simva = can.Bus(interface='simva', channel=8)
    print('Initialize')
    while True:
        ''' Recv from SimVA '''
        msg = simva.recv()
        print(f'recv = {msg.arbitration_id}')
    
        ''' send to remote-can for visualization '''
        bus.send(msg)
    
        ''' Send to SimVA '''
        time.sleep(0.1)
        for base in [0x400, 0x410, 0x420, 0x430, 0x440, 0x450, 0x460, 0x470, 0x480]:
            for i in range(2):
                id = base + i
                data = [255, 255, 255, 255, 255, 255, 255, 255]
    
                simva.send(can.Message(arbitration_id=id, data=data))
    

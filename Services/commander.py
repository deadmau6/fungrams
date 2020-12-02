from subprocess import Popen, PIPE, STDOUT, TimeoutExpired
import os, sys, time, threading, queue, signal

class Commander:
    """This starts, stops, and manages processes on the OS."""
    def __init__(self):
        pass

    @staticmethod
    def check_server(server, port):
        nc = Popen(["nc", "-zv", server, port], stdout=PIPE, stderr=PIPE)
        is_success = (nc.communicate()[1].find(b'failed') == -1)
        return is_success

    def _handle_signal(sig_num, frame_stack):
        # Handles a termination signal from the user.
        print('\nRecieved signal: {}'.format(sig_num))
        raise Exception("Shutting down...")

    def _output_reader(proc, outq):
        # Continuely reads stdout from proc.
        for line in iter(proc.stdout.readline, b''):
            # Adds the stdout to the queue.
            outq.put(line.decode('utf-8'))

    def inline_process(self, command, path=None, env=None):
        print('"Ctrl-C" to end the process:')
        # Creates the process and sets the stdout.
        proc = Popen(command, cwd=path, env=env, stdout=PIPE, stderr=STDOUT)
        # Set up the sinal handlers for the thread before it is created.
        signal.signal(signal.SIGTERM, CommandService._handle_signal)
        signal.signal(signal.SIGINT, CommandService._handle_signal)
        # Create queue.
        outq = queue.Queue()
        # Wait for signal interrupt.
        try:
            # Create a separate thread for reading output.
            t = threading.Thread(target=CommandService._output_reader, args=(proc, outq))
            # Start the thread
            t.start()
            # Wait for node app to startup.
            time.sleep(0.2)
            # Loop endlessly printing out server response.
            while True:
                line = outq.get()
                # If the queue is empty then the process stopped.
                if line is None:
                    raise Exception("Shutting down...")
                # Print out server response.
                print(line)
                time.sleep(0.1)

        except Exception as e:
            # Shutdown the process and thread safely.
            print(e)
            # Stop the process.
            proc.terminate()
            try:
                # Be sure it truely stopped (ie nothing blocked proc.terminate).
                proc.wait(timeout=0.2)
                print('--- process exited with code: {} ---'.format(proc.returncode))
            except TimeoutExpired:
                print('Process did not terminate in time')
            # Stop the thread.
            t.join()

    @staticmethod
    def run(command, op_name='User command', path=None, env=None, timeout=60):
        proc = Popen(command, cwd=path, env=env)
        try:
            rc = proc.wait(timeout=timeout)
            return rc
        except TimeoutExpired:
            proc.kill()
            print('\n{} timed out after {} seconds'.format(op_name, timeout))
            return -1
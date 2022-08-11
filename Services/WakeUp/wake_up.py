from ..Config import Configuration
from ..commander import Commander
from ..pretty_term import cprint

class WakeUp:
    """Manage and run user defined commands from a single source"""
    def __init__(self, **kwargs):
        super().__init__()
        self.section_name = 'WAKEUP'
        self.config = Configuration()
        self._setup_check()

    def _create_default(self):
        self.config.set_entry(self.section_name, 'default', '0', True, False)
        self.config.set_entry(self.section_name, '0', "echo 'Running default commands:'", True, True)
        # If there were no errors in the previous lines then this should not error.
        err, sect = self.config.get_section(self.section_name)

    def _setup_check(self):
        """Check that this has been setup, if not create defaults."""
        err, sect = self.config.get_section(self.section_name)
        if err or 'default' not in sect:
            self._create_default()

    def get_config(self):
        err, sect = self.config.get_section(self.section_name)
        if err:
            self._create_default()
        return sect

    def _run_command(self, cmd, timeout):
        return Commander.run(
            cmd.get('command'),
            cmd.get('op_name', 'User command'),
            cmd.get('path'),
            cmd.get('env'),
            timeout)

    def _clean_command(self, cmd_string):
        # prevent recursion?
        if 'wakeup' in cmd_string or 'wake_up.py' in cmd_string:
            raise Exception("Sorry cannot run commands with 'wakeup' or 'wake_up.py' in order to prevent recursive behavior.")
        else:
            # The _run_command function(from Commander.run) requires that the command be a list of strings 
            return cmd_string.split(' ')

    def _process_command(self, cmd_key, timeout, config):
        # Runs an individual command
        if config.get(cmd_key):
            # clean and make sure the command is safe?
            clean_cmd = self._clean_command(config.get(cmd_key))
            # Set the operation name
            # Pre-append fungrams_wakeup so user can know it was run from this module
            op_name = f"fungrams_wakup : {cmd_key}"
            # run the command
            retcode = self._run_command({'command': clean_cmd, 'op_name': op_name}, timeout)
            if retcode == 0:
                cprint(f"{cmd_key} : completed!", 'bold', 'green')
            else:
                cprint(f"{cmd_key} : failed with code {retcode}", 'bold', 'light_red')
        else:
            raise Exception(f"Error: Could not found find {cmd_key}")

    def process_single_command(self, cmd_key, timeout):
        cmds_object = self.get_config()
        self._process_command(cmd_key, timeout, cmds_object)

    def process_group_command(self, group_key, timeout):
        # Runs a command group which is just an ordered string of command keys separated with semicolons
        cmds_object = self.get_config()
        if cmds_object.get(group_key):
            # command group should be separated with semicolons
            cmds = cmds_object.get(group_key).split(';')
            for cmd in cmds:
                # prevent recursion, but this wouldn't work anyways bc it would be improperly parsed
                if cmd == group_key:
                    continue
                self._process_command(cmd, timeout, cmds_object)
        else:
            raise Exception(f"Error: Command {group_key} not found in config {list(cmds_object.keys())}")

    def add_command(self, cmd_key, cmd_string, overwrite=False, immediate_update=True):
        if ';' in cmd_key:
            raise Exception("No Semicolons are allowed in the command name.")
        clean_cmd = self._clean_command(cmd_string)
        clean_string = ' '.join([_ for _ in clean_cmd])
        # Returns: (is_error, response)
        return self.config.set_entry(self.section_name, cmd_key, clean_string, overwrite, immediate_update)

    def add_group_command(self, group_key, cmds_list, overwrite=False, immediate_update=True):
        if ';' in group_key:
            raise Exception("No Semicolons are allowed in the group command name.")
        group_config = self.get_config()
        for cmd_key in cmds_list:
            if cmd_key not in group_config:
                raise Exception(f"Error: Could not find command {cmd_key}")
            if ';' in cmd_key:
                raise Exception("No Semicolons are allowed in the command name.")
        cmds_string = ';'.join([_ for _ in cmds_list])
        return self.config.set_entry(self.section_name, group_key, cmds_string, overwrite, immediate_update)


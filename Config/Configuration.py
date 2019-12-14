import os, sys, time, configparser

class Configuration:
    """This Class gets and sets user defined constants to a local ini file."""
    def __init__(self, initial_config=None):
        """Try to get the local config file from a static/user defined location.
        
        If the location of the parent folder is defined in the user's env (also see `aliases.backup` ~ line 7)
        then the 'config.local.ini' will be placed there which should be the directory that `fun_shell.py` is in.
        Otherwise the `config.local.ini` will be constructed in THIS folder.
        """
        if os.getenv('FGRMS'):
            self.local_config_path = os.path.join(os.getenv('FGRMS'), 'config.local.ini')
        else:
            self.local_config_path = os.path.join(os.getcwd(), 'config.local.ini')
        # For redundency check that the path actually exists and if it doesn't then create it!
        if not os.path.exists(self.local_config_path):
            Configuration.create_config(self.local_config_path, initial_config)

        self.config = configparser.ConfigParser()
        self.config.read_file(open(self.local_config_path))

    def _update_config(self):
        """Updates the local configuration on disk by writing it to the config.local.ini file."""
        with open(self.local_config_path, 'w+') as f:
            self.Config.write(f)

    def get_section(self, section):
        """Get the provided section as an object.

        Returns - ( is_error(bool), section_dict or error_message )."""
        if self.config.has_section(section):
            sect_obj = {}
            for k, v in self.Config.items(section):
                sect_obj[k] = v
            return False, sect_obj
        else:
            # TODO, return error in some way or something else.
            return True, f'Section: [{section}] does not exist. Availble sections: {self.config.sections()}')

    def get_entry(self, section, entry):
        """Gets the value from a valid entry, given the section name and entry name.

        Returns - ( is_error(bool), entry_value or error_message )."""
        error, sect = self.get_section(section)
        if error:
            return error, sect
        try:
            value = sect[entry]
            return False, value
        except KeyError:
            return True, f'Entry: [{entry}] in Section: [{section}] does not exist.'

    def set_section(self, section, immediate_update=True):
        """Add a single empty section to the config.

        Returns - ( Boolean if section exists, Message string )."""
        try:
            # Adds a new section.
            self.config.add_section(section)
            # Immediately writes config to disk.
            if immediate_update:
                self._update_config()
            return True, f'Successfully added section [{section}]'

        except configparser.DuplicateSectionError:
            return True, f'Warning: {section} already exists. Current sections: {self.config.sections()}.'
        except TypeError, ValueError:
            # This is a genuine error and this entire section cannot be added.
            return False, f"Failed to add section {section}. Check to be sure it is the correct Type(string) and that it is NOT 'Default' which is a key word and cannot be used!"

    def set_entry(self, section, entry, value, overwrite=False, immediate_update=True):
        """Adds or overwrites the Entry and Value provided, under the given section.

        Returns - ( Boolean if entry was set, Message string )."""
        section_exists, msg = self.set_section(section, False)
        if not section_exists:
            return section_exists, msg
        
        # 'error' should be true only if the entry does not exist!
        error, val = self.get_entry(section, entry)
        if error or overwrite:
            self.config.set(section, entry, value)
            if immediate_update:
                self.update_config()
            return True, f'Successfully added entry [{section}] {entry} = {value}'
        # Do not overwrite the entry.
        return False, f'Warning: {entry} already exists with {val}.'

    def add_entries(self, section, entries, immediate_update=True):
        if not isinstance(entries, dict):
            return False, f"Entries must be a dict not a {type(entries)}."
        
        section_exists, msg = self.set_section(section, False)
        if not section_exists:
            return section_exists, msg
        
        existing_entries = {}
        for entry, value in entries.items():
            err, v = self.get_entry(section, entry)
            if err:
                # Entry does not exist so we can add it safely.
                is_set, msg = self.set_entry(section, entry, value, False, False)
                print(msg)
            else:
                existing_entries[entry] = v
        
        if len(existing_entried.keys()) == 0:
            # All entries where added.
            return True, f'succ'

        print(f'There are {len(existing_entries.keys())} entries that already exist.')
        print('Would you like to overwrite all of them(y), None of them(n), or select each one to overwrite(s)?')
        overwrite_all = 0
        while True:
            time.sleep(0.1)
            answer = sys.stdin.readline()
            if answer[0] == 'y':
                overwrite_all = 1
                break
            elif answer[0] =='n':
                overwrite_all = -1
                break
            elif answer[0] =='s':
                overwrite_all = 0
                break
            else:
                print('Please answer with "yes", "no", or "select"')
        


    @staticmethod
    def create_config(file_path, options=None):
        """If the local config file does not exist then create the file."""
        if os.path.exists(file_path):
            raise Exception(f"File already exists at {file_path}, try using merge or provide a different file.")
        
        # Create a new local configuration.
        initial = configparser.ConfigParser()
        initial.add_section('OS')
        initial.set('OS', 'type', sys.platform)
        initial.add_section('PATHS')
        initial.set('PATHS', 'home', os.getenv('HOME'))

        # Add the provided options which should be formatted as { Section: { Entry: Value, } }.
        if options and isinstance(options, dict):
            # Display any failed sections or entries after parsing the user's options.
            errors = []
            warnings = []
            for section in options.keys():
                try:
                    if initial.has_section(section):
                        warnings.append(f"Section: {section}, already exists.")
                    else:
                        initial.add_section(section)
                    if not isinstance(options[section], dict):
                        raise Exception(f"{section} must be of type 'dict' and not {type(options[section])}.") 

                except TypeError, ValueError:
                    # This is a genuine error and this entire section cannot be added.
                    errors.append(f"Failed to add section {section}. Check to be sure it is the correct Type(string) and that it is NOT 'Default' which is a key word and cannot be used!")
                except Exception as e:
                    errors.append(e)
                else:
                    for entry, value in options[section].items():
                        # DO NOT OVERWRITE.
                        if initial[section].get(entry):
                            warnings.append(f"Entry: {section} - {entry} already has a value and will be skipped. Use merge to overwrite this value.")
                        else:
                            initial.set(section, entry, value)
            # Display the warnings and errors.
            for w in warnings:
                print(f"WARNING: {w}")
            for e in errors:
                print(f"ERRORS: {e}")
            
        # Writes the config to local.ini.
        with open(file_path, 'w+') as f:
            initial.write(f)

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

        Returns - ( is_error [Boolean], section_dict [Dict] or error_message [String])."""
        if self.config.has_section(section):
            sect_obj = {}
            for k, v in self.Config.items(section):
                sect_obj[k] = v
            return False, sect_obj
        else:
            # TODO, return error in some way or something else.
            return True, f'Section: [{section}] does not exist. Availble sections: {self.config.sections()}'

    def get_entry(self, section, entry):
        """Gets the value from a valid entry, given the section name and entry name.

        Returns - ( is_error [Boolean], entry_value [String] or error_message [String] )."""
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

        Returns - ( section_exists [Boolean], message [String] )."""
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

        Returns - ( entry_set [Boolean], message [String] )."""
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

    def _add_entries(self, section, entries, overwrite=False):
        """Add an entries object to a given section.

        Warning this DOES NOT write the changes to disk!
        Also this is a private method and should not be used directly.
        Returns - ( success[Boolean], message[String] )."""
        if not isinstance(entries, dict):
            return False, f"Entries must be a dict not a {type(entries)}."

        section_exists, msg = self.set_section(section, False)
        if not section_exists:
            return section_exists, msg
        
        existing = {}
        for entry, value in entries.items():
            no_entry, v = self.get_entry(section, entry)
            if no_entry or overwrite:
                # Entry does not exist so we can add it safely.
                is_set, msg = self.set_entry(section, entry, value, False, False)
                print(msg)
            else:
                existing[entry] = v
        
        if len(existing.keys()) == 0:
            # All entries where added.
            return True, "Successfully added all of the entries."

        print(f'There are {len(existing_entries.keys())} entries that already exist.')
        print('Would you like to overwrite all of them(y), None of them(n), or select each one to overwrite(s)?')
        overwrite_choice = 0
        while True:
            time.sleep(0.1)
            answer = sys.stdin.readline().lower()
            if answer[0] == 'y':
                overwrite_choice = 1
                break
            elif answer[0] =='n':
                overwrite_choice = -1
                break
            elif answer[0] =='s':
                overwrite_choice = 0
                break
            else:
                print('Please answer with "yes"(y), "no"(n), or "select"(s)')
        # Don't overwrite anything!
        if overwrite_choice < 0:
            return True, f"User decided not to overwrite existing entries."
        # Overwrite All of the existing entries.
        if overwrite_choice > 0:
            for entry in existing.keys():
                value = entries[entry]
                is_set, msg = self.set_entry(section, entry, value, True, False)
                print(msg)
            return True, f"All existing entries have been overwritten."
        # User Selects which entries to overwrite.
        while True:
            
            if len(existing.keys()) == 0:
                break
            time.sleep(0.1)

            entry = existing.keys()[0]
            current_val = existing[entry]
            overwrite_val = entries[entry]

            print(f'Do you want to overwrite {entry}: {current_val} with {overwrite_val}? [y/n]')
            answer = sys.stdin.readline().lower()
            
            if answer[0] == 'y':
                existing.pop(entry)
                is_set, msg = self.set_entry(section, entry, overwrite_val, True, False)
                print(msg)
            elif answer[0] =='n':
                existing.pop(entry)
                print(f"Keeping {entry} as {current_val}.")
            else:
                print('Please answer with "yes"(y), "no"(n)')
        return True, "All entries have been successfully added."

    def add_entries(self, section, entries, overwrite=False):
        """Add all of the provided entries(dict) under the given section."""
        success, message = self._add_entries(section, entries, overwrite)
        print(message)
        if success:
            print(f"Writing entries to file {self.local_config_path}.")
            self._update_config()
        else:
            print(f"Error found, Cannot write changes to disk!")

    def add_sections(self, sections, overwrite=False):
        """Adds multiple sections to the config.
        
        If sections is an array then just the empty sections are added.
        If sections is a dict then it is assumed the entries are also a dict and will be added."""
        if isinstance(sections, dict):
            for sect, entries in sections.items():
                # _add_entries() will also add the section and verify that entries is a dict.
                sucess, message = self._add_entries(sect, entries, overwrite)
                if success:
                    print(f"Successfully created Section: {sect}.")
                else:
                    print("Error! Could not create section, for the following reason:")
                    print(message)
            print(f"Writing sections to file {self.local_config_path}.")
            self._update_config()
            return True

        if isinstance(sections, list):
            for sect in sections:
                success, message = self.set_section(sect, False)
                if success:
                    print(f"Successfully created Section: {sect}.")
                else:
                    print("Error! Could not create section, for the following reason:")
                    print(message)
            print(f"Writing sections to file {self.local_config_path}.")
            self._update_config()
            return True
        print("ERROR: Sections is not correct Type!")
        print("Pls set sections to be either an object like this \{ SECT: \{ ENTRY: VALUE \} \} or an array of strings.")
        return False

    def delete_section(self, section):
        """Delete the entire given section."""
        if show_section(section):
            print('Are you sure you wish to delete this section?(y/n)')
            while True:
                time.sleep(0.2)
                answer = sys.stdin.readline()
                if answer[0] == 'y':
                    self.config.remove_section(section)
                    self._update_config()
                    print(f'Deleted section: {section}')
                    break
                elif answer[0] =='n':
                    print(f'Exited without deleting {section}')
                    break
                else:
                    print('Please answer with "yes" or "no"')

    def delete_entry(self, section, entry):
        """Delete a single entry given the section and entry."""
        error, value = self.get_entry(section, entry)
        if not error:
            print(f'Found entry [{section}] {entry} = {value}')
            print('Are you sure you wish to delete this entry?(y/n)')
            while True:
                time.sleep(0.2)
                answer = sys.stdin.readline()
                if answer[0] == 'y':
                    self.config.remove_option(section, entry)
                    self._update_config()
                    print(f'Deleted entry: [{section}] {entry} = {value}')
                    break
                elif answer[0] =='n':
                    print(f'exited without deleting [{section}] {entry} = {value}')
                    break
                else:
                    print('Please answer with "yes" or "no"')
        else:
            print(value)

    def show_section(self, section):
        """Print out the provided section."""
        error, sect = self.get_section(section)
        if not error:
            print(section)
            for k,v in sect.items():
                print(f'\t{k} = {v}')
            return True
        else:
            print(sect)
            return False

    def show_config(self):
        """Print out the entire config file."""
        for sect in self.config.sections():
            print(sect)
            for k, v in self.config.items(sect):
                print(f'\t{k} = {v}')

    def start(self, args):
        pass

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

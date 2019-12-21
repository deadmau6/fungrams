import os
import sys
import json
import time
import configparser

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
            self.config.write(f)

    def get_section(self, section):
        """Get the provided section as an object.

        Returns - ( is_error [Boolean], section_dict [Dict] or error_message [String])."""
        if self.config.has_section(section.upper()):
            sect_obj = {}
            for k, v in self.config.items(section.upper()):
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
            self.config.add_section(section.upper())
            # Immediately writes config to disk.
            if immediate_update:
                self._update_config()
            return True, f'Successfully added section [{section}]'

        except configparser.DuplicateSectionError:
            return True, f'Warning: {section} already exists. Current sections: {self.config.sections()}.'
        except (TypeError, ValueError):
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
            self.config.set(section.upper(), entry, value)
            if immediate_update:
                self._update_config()
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

        print(f'There are {len(existing.keys())} entries that already exist.')
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
        existing_entries = list(existing.keys())
        while True:
            
            if len(existing_entries) == 0:
                break
            time.sleep(0.1)

            entry = existing_entries[-1]
            current_val = existing[entry]
            overwrite_val = entries[entry]

            print(f'Do you want to overwrite {entry}: {current_val} with {overwrite_val}? [y/n]')
            answer = sys.stdin.readline().lower()
            
            if answer[0] == 'y':
                existing_entries.pop(-1)
                is_set, msg = self.set_entry(section, entry, overwrite_val, True, False)
                print(msg)
            elif answer[0] =='n':
                existing_entries.pop(-1)
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
                success, message = self._add_entries(sect, entries, overwrite)
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
        if self.show_section(section):
            print('Are you sure you wish to delete this section?(y/n)')
            while True:
                time.sleep(0.2)
                answer = sys.stdin.readline()
                if answer[0] == 'y':
                    self.config.remove_section(section.upper())
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
                    self.config.remove_option(section.upper(), entry)
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

    def merge(self, current, target=None, output=None, verbose=False):
        """This will take the values in 'current' config and apply then to the 'target' config.

        Nothing in the 'target' config is overwritten! Only new changes are added.
        If 'target' is blank then the local config is used by default.
        Both 'current' and 'target' can be file paths to other configs or a string representation of configs.
        If 'target' is a string representation then 'output' SHOULD be provided so the config can write to disk.
        If 'output' is not given the config will attempt to write to the home directory!"""
        changes_config = configparser.ConfigParser()
        if os.path.exists(current):
            changes_config.read_file(open(current))
        else:
            try:
                changes_config.read_string(current)
            except configparser.MissingSectionHeaderError as e:
                print(current)
                print(e)
                raise Exception(f"File not found, attempted to read data as Sting which then errored: {e}.")
        result_config = None
        if not target:
            result_config = self.config
        elif os.path.exists(target):
            result_config = configparser.ConfigParser()
            result_config.read_file(open(target))
        else:
            result_config = configparser.ConfigParser()
            try:
                result_config.read_string(target)
            except configparser.MissingSectionHeaderError as e:
                print(target)
                print(e)
                raise Exception(f"File not found, attempted to read data as Sting which then errored: {e}.")
        result_config = Configuration.merge_configs(changes_config, result_config, verbose)
        if not target:
            with open(self.local_config_path, 'w+') as f:
                result_config.write(f)
        elif os.path.exists(target):
            with open(target, 'w+') as f:
                result_config.write(f)
        elif os.path.exists(output):
            with open(output, 'w+') as f:
                result_config.write(f)
        else:
            home = os.path.join(os.getenv('HOME'), 'fungrams.config.ini')
            print(f'Output: {output} not found, attempting to write to HOME: {home}.')
            with open(home, 'w') as f:
                result_config.write(f)

    def start(self, args):
        if args.list_section:
            # List all sections
            if isinstance(args.list_section, int):
                self.show_config()
            else:
                self.show_section(args.list_section)
        elif args.set:
            size = len(args.set)
            if size == 1:
                # Adds a new section to local.ini.
                self.set_section(args.set[0])
            elif size == 3:
                # Adds/updates an entry in local.ini.
                self.set_entry(args.set[0], args.set[1], args.set[2], overwrite=args.force)
            elif size > 3:
                print(f"To many args found, only attempting to set these values: {args.set[:3]}.")
                # Adds/updates an entry in local.ini.
                self.set_entry(args.set[0], args.set[1], args.set[2], overwrite=args.force)
            else:
                print(f"ERROR: Not enough Arguements provided. 1 or 3 are required but only recieved {size} - {args.set}.")
        elif args.delete:
            size = len(args.delete)
            if size == 1:
                # Removes section from local.ini.
                self.delete_section(args.delete[0])
            elif size > 2:
                print(f"To many args found, only attempting to remove these values: {args.delete[:2]}.")
                # Removes entry from local.ini.
                self.delete_entry(args.delete[0], args.delete[1])
            else:
                # Removes entry from local.ini.
                self.delete_entry(args.delete[0], args.delete[1])
        elif args.merge:
            size = len(args.merge)
            # Merges given config into the local config.
            if size > 3:
                print(f"To many args found, only attempting to use these values: {args.merge[:3]}.")
                self.merge(args.merge[0], args.merge[1], args.merge[2])
            elif size == 3:
                self.merge(args.merge[0], args.merge[1], args.merge[2])
            elif size == 2:
                self.merge(args.merge[0], args.merge[1])
            else:
                self.merge(args.merge[0])
        elif args.data:
            cleaned = None
            if os.path.exists(args.data):
                # Everything is parsed in as a string.
                cleaned = json.load(args.data, parse_int=str, parse_float=str, parse_constant=str)
            else:
                # Everything is parsed in as a string.
                cleaned = json.loads(args.data, parse_int=str, parse_float=str, parse_constant=str)
            self.add_sections(cleaned, overwrite=args.force)
        else:
            # Default show config.
            self.show_config()

    @staticmethod
    def merge_configs(changes, result, verbose=False):
        """Given that 'changes' and 'results' are ConfigParser object's, this will apply 
        the absent changes from 'changes' into 'result'.

        Therefore 'result' keeps all of 'result' and then gets whatever is new in 'changes'.
        The flag 'verbose' just prints out all of the values in 'changes' that were not written.
        Returns - merged_result [configparser.ConfigParser] ."""
        if not isinstance(changes, configparser.ConfigParser):
            raise Exception(f"ERROR: 'changes' must be an instance of {type(configparser.ConfigParser())} not of {type(changes)}.")
        if not isinstance(result, configparser.ConfigParser):
            raise Exception(f"ERROR: 'result' must be an instance of {type(configparser.ConfigParser())} not of {type(result)}.")
        skipped = {}
        for section in changes.sections():
            if not result.has_section(section.upper()):
                result.add_section(section.upper())
            for entry, value in changes.items(section):
                if result.has_option(section.upper(), entry):
                    if section in skipped:
                        skipped[section].append(entry)
                    else:
                        skipped[section] = [entry]
                else:
                    result.set(section.upper(), entry, value)
        if verbose:
            print('Successfully merged configs.')
            if len(skipped.keys()) > 0:
                print('The following entries were NOT changed. To overwrite them try manually adding the entries with "--force".')
                for sect, entries in skipped.items():
                    print(f"For Section [{sect}]:")
                    print(f"\t{entries}")
        return result 

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
                    if initial.has_section(section.upper()):
                        warnings.append(f"Section: {section}, already exists.")
                    else:
                        initial.add_section(section.upper())
                    if not isinstance(options[section], dict):
                        raise Exception(f"{section} must be of type 'dict' and not {type(options[section])}.") 

                except (TypeError, ValueError):
                    # This is a genuine error and this entire section cannot be added.
                    errors.append(f"Failed to add section {section}. Check to be sure it is the correct Type(string) and that it is NOT 'Default' which is a key word and cannot be used!")
                except Exception as e:
                    errors.append(e)
                else:
                    for entry, value in options[section].items():
                        # DO NOT OVERWRITE.
                        if initial[section.upper()].get(entry):
                            warnings.append(f"Entry: {section} - {entry} already has a value and will be skipped. Use merge to overwrite this value.")
                        else:
                            initial.set(section.upper(), entry, value)
            # Display the warnings and errors.
            for w in warnings:
                print(f"WARNING: {w}")
            for e in errors:
                print(f"ERRORS: {e}")
            
        # Writes the config to local.ini.
        with open(file_path, 'w+') as f:
            initial.write(f)

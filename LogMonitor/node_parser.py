from .parser import Parser
from .log_object import NodeLog

class NodeParser(Parser):

    def __init__(self):
        super().__init__()
        self.entry_num = 0
        self.error_keywords = ['Error', 'AssertionError', 'RangeError', 'ReferenceError', 'SyntaxError', 'TypeError']

    def _skip_line(self):
        line_num = self.current.line
        while self.current.line == line_num:
            self.match(None)
            if self.current is None:
                break

    def _get_raw_line(self):
        raw_line = []
        line_num = self.current.line
        while self.current.line == line_num:
            raw_line.append(self.match(None))
            if self.current is None:
                break
        return raw_line

    def _next_entry(self):
        # Start at the begining of the next line.
        self._skip_line()
        if self.current is None:
            return True
        # Each entry starts with a timestamp.
        while self.current.typ != 'NUMBER':
            self._skip_line()
            if self.current is None:
                break
        return True

    def parse(self, tokens):
        self.tokens = tokens
        self.advance()
        while self.current is not None:
            yield self._log_entry()

    def _log_entry(self):
        self.entry_num += 1
        line = self.current.line
        timestamp = self._timestamp()
        level = self._level()
        status = self._http_status()
        message = self._node_message()
        error = self._error_entry(status) if level == 'error' else None
        return NodeLog(self.entry_num, line, timestamp, level, status, message, error)

    def _error_entry(self, status):
        if status:
            return self._api_error()
        return self._node_error()
    
    def _api_error(self):
        trace = self._trace()
        self.match('WORD', value='Stack')
        self.match('COLON')
        stack = self._api_stack()
        return { 'trace': trace, 'stack': stack }

    def _node_error(self):
        error_cls_name = self.match('WORD')

        error_code = self._error_code() if self.current.typ == 'SBRACKET' else None

        if self.current.typ != 'COLON':
            return self._compile_time_error(error_cls_name)
        
        self.match('COLON')

        stack = self._stack(error_cls_name)
        #Skip the trace cause we don't need it.
        self.match('WORD', 'Trace')
        self._skip_line()
        #Skip the stack cause we already have it.
        self.match('WORD', 'Stack')
        self._skip_line()

        if error_cls_name == 'SyntaxError':
            while not self._is_stack_frame():
                self._skip_line()
                if self.current is None:
                    break

        while self._is_stack_frame():
            self._skip_line()
            if self.current is None:
                break
        return {
            'name': error_cls_name,
            'code': error_code,
            'stack': stack, 
        }

    def _compile_time_error(self, error_cls_name):
        msg_size, ct_error, ct_code, ct_message = self._compile_time_message(error_cls_name)

        ct_stack = self._compile_time_stack(ct_error, msg_size)
        #Skip the trace cause we don't need it.
        self.match('WORD', 'Trace')
        for i in range((msg_size + 1)):
            self._skip_line()

        #Skip the stack cause we already have it.
        self.match('WORD', 'Stack')
        for i in range((msg_size + 1)):
            self._skip_line()

        while self._is_stack_frame():
            self._skip_line()
            if self.current is None:
                break

        return {
            'name': ct_error,
            'code': ct_code,
            'compile_time': ct_message,
            'stack': ct_stack,
        }

    def _compile_time_stack(self, error_name, msg_size):
        error_msg = self._node_message()

        stack_frames = []

        # Skip past the compile time error
        for i in range(msg_size):
            self._skip_line()
        
        while self._is_stack_frame():
            stack_frames.append(self._stack_frame())
            if self.current is None:
                break

        return {
            'Name': error_name,
            'Message': error_msg,
            'Frames': stack_frames
        }

    def _compile_time_message(self, first_word):
        ct_msg = [first_word]
        ct_msg.extend(self._get_raw_line())
        ct_error_name = ''
        ct_error_code = None
        message_size = 1
        while True:
            new_line_start = self.match('WORD')
            bracket_code = None
            if self.current.typ == 'SBRACKET':
                bracket_code = self._error_code()
            if self.current.typ == 'COLON':
                self.match('COLON')
                ct_error_name = new_line_start
                ct_error_code = bracket_code
                break
            ct_msg.append(new_line_start)
            if bracket_code:
                ct_msg.extend(['[', bracket_code, ']'])
            ct_msg.extend(self._get_raw_line())
            message_size += 1
            if self.current == None:
                break
        return message_size, ct_error_name, ct_error_code, ' '.join(ct_msg) 

    def _api_stack(self):
        error_cls_name = self.match('WORD')
        
        self.match('COLON')
        
        error_msg = self._node_message()
        
        stack_frames = []

        while self._is_stack_frame():
            stack_frames.append(self._stack_frame())
            if self.current is None:
                break
        return {
            'Name': error_cls_name,
            'Message': error_msg,
            'Frames': stack_frames,
        }

    def _stack(self, error_name):

        error_msg = self._node_message()

        syntax_error_block = self._syntax_block() if error_name == 'SyntaxError' else None
        
        stack_frames = []

        while self._is_stack_frame():
            stack_frames.append(self._stack_frame())
            if self.current is None:
                break
        return {
            'Name': error_name,
            'Message': error_msg,
            'Frames': stack_frames,
            'Block': syntax_error_block
        }

    def _syntax_block(self):
        block = []
        
        while not self._is_stack_frame():
            if self.current.typ == 'PIPE':
                self._skip_line()
            block.append(self._syntax_block_line())
            if self.current is None:
                break

        return '\n'.join(block)

    def _syntax_block_line(self):
        marigin = []

        code = []

        found_pipe = False
        
        line_num = self.current.line
        while self.current.line == line_num:
            if found_pipe:
                code.append(self.match(None))
            else:
                found_pipe = self.current.typ == 'PIPE'
                marigin.append(self.match(None))
            if self.current is None:
                break

        return f"{' '.join(marigin)} {''.join(code)}"

    def _error_code(self):
        self.match('SBRACKET')
        code = []
        while self.current.typ != 'SBRACKET':
            code.append(self.match(None))
        self.match('SBRACKET')
        return ''.join(code)

    def _is_stack_frame(self):
        return self.current.typ == 'WORD' and (self.current.value == 'at' or self.current.value == 'From')

    def _stack_frame(self):
        self.match('WORD')
        frame_name = []
        location = None
        line_num = self.current.line
        while self.current.line == line_num:
            if self.current.typ == 'FSLASH':
                # Might be a file location.
                location = self._sframe_location()

            elif self.current.typ == 'PAREN' and self.current.value == '(':
                # Either File location or part of name.
                frame_name.append(self.match('PAREN'))
                is_loc, paren_stmt = self._sframe_paren()
                if is_loc:
                    location = paren_stmt
                    frame_name.pop()
                    self.match('PAREN')
                else:
                    frame_name.append(paren_stmt[0])
                    frame_name.append(self.match('PAREN'))

            elif self.current.typ == 'DOT':
                # Could be file name.
                frame_name.append(self.match('DOT'))
                if self._is_sframe_file():
                    frame_name.append(self.match('WORD'))
                    _, line, column = self._sframe_location()
                    location = (''.join(frame_name), line, column)
                    frame_name = []
                else:
                    frame_name.append(self.match(None))

            else:
                frame_name.append(self.match(None))
            if self.current is None:
                break

        return ''.join(frame_name), location

    def _sframe_paren(self):
        location = False
        f_name = []
        line = None
        column = ''
        while self.current.typ != 'PAREN':
            if self.current.typ == 'DOT':
                # Could be a file location.
                f_name.append(self.match('DOT'))

                if self._is_sframe_file():
                    # Is a file location.
                    location = True
                    f_name.append(self.match('WORD'))
                    _, line, column = self._sframe_location()

                else:
                    f_name.append(self.match(None))

            else:
                f_name.append(self.match(None))
        
        return location, (''.join(f_name), line, column)

    def _sframe_location(self):
        colon_count = 0
        location = [[], [], []]
        while colon_count != 2:
            if self.current.typ == 'COLON':
                self.match('COLON')
                colon_count += 1
            location[colon_count].append(self.match(None))

        return (''.join(location[0]), location[1], location[2])

    def _is_sframe_file(self):
        return self.current.typ == 'WORD' and self.current.value == 'js'

    def _trace(self):
        self.match('WORD', value='Trace')
        self.match('COLON')
        self.match('CBRACKET')
        trace = {}
        while self.current.typ != 'CBRACKET':
            key = self.match('WORD')
            self.match('COLON')
            value = self._trace_value()
            trace[key] = value if value else 'null'
        self.match('CBRACKET')
        return trace

    def _trace_value(self):
        value = []
        while self.current.typ != 'COMMA':
            value.append(self.match(None))
            if self.current.typ == 'CBRACKET':
                return ''.join(value)
        self.match('COMMA')
        return ''.join(value)

    def _node_message(self):
        if self.current is None:
            return "empty message"
        msg = []
        line_num = self.current.line
        while self.current.line == line_num:
            msg.append(self.match(None))
            if self.current is None:
                break
        return ' '.join(msg)

    def _http_status(self):
        if self.current.typ == 'COLON':
            return None
        self.match('SBRACKET')
        stat = self.match('NUMBER')
        self.match('SBRACKET')
        return stat

    def _level(self):
        return self.match('WORD')

    def _timestamp(self):
        date = self._isodate()
        time = self._ntime()
        return (date, time)

    def _ntime(self):
        hr, (mi, sec) = self._nhour()
        return (hr, mi, sec)

    def _nhour(self):
        hr = self.match('NUMBER')
        self.match('COLON')
        return hr, self._nminute()

    def _nminute(self):
        mi = self.match('NUMBER')
        self.match('COLON')
        return mi, self._nsec()

    def _nsec(self):
        return self.match('NUMBER')

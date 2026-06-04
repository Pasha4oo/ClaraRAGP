class GarbageDestroyer(object):
    def __init__(self):
        pass

    def destroy_xaml(self, message: str) -> str:
        '''
        Removes garbage xaml metadata
        <xamlTags>DATA</xamlTags>
        '''

        message = str(message)

        while ((start_index := message.find("<")) != -1) and ((end_index := message.find(">")) != -1):
            print(1)
            tag = message[start_index + 1:end_index]

            close_tag = f"</{tag}>"
            close_tag_index = message.find(close_tag)

            if close_tag_index != -1:
                message = message[:start_index] + message[close_tag_index + len(close_tag):]
            elif (start_index != -1) and (end_index != -1):
                message = message[:start_index] + message[end_index + 1:]

        return message.strip()

    def destroy_functions(self, message: str) -> str:
        '''
        Removes garbage functions metadata
        [func_name1(params_name1=params_value1, params_name2=params_value2...), func_name2(params)]
        '''
        while ((start_index := message.find("[")) != -1) and ((end_index := message.find("]")) != -1):
            message = message[:start_index] + message[end_index + 1:]

        return message.strip()

    def destroy_all(self, message: str) -> str:
        '''
        Removes garbage metadata from ai messages

        <xamlTags>DATA</xamlTags>
        [func_name1(params_name1=params_value1, params_name2=params_value2...), func_name2(params)]
        '''

        message = self.destroy_xaml(message)
        message = self.destroy_functions(message)

        return message
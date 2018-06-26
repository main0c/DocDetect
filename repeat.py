from threading import Timer,Thread,Event


class RepeatTimer:

   def __init__(self, time, function):
      self.time = time
      self.function = function
      # self.args = args
      self.thread = Timer(self.time, self.action)

   def action(self):
       # self.function(self.args)
       self.function()
       self.thread = Timer(self.time, self.action)
       self.thread.start()

   def start(self):
      self.thread.start()

   def cancel(self):
      self.thread.cancel()

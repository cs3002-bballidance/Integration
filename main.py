from multiprocessing import Process
#import prediction
import mega_pi_integrated
import client

#def prediction_process():
	#prediction.main_loop()

def write_data_process():
	#call write data function
	client.createClient('172.17.105.245',8888)
	#pass

def mega_process():
	mega_pi_integrated.start_running()


if __name__ == '__main__':
	#Process(target=prediction_process).start()
	Process(target=write_data_process).start()
	Process(target=mega_process).start()

# Integration
This repo contains the integration code.  

---

## Miscellaneous info

To access the remote pi for testing:  
On terminal - `ssh <username>@bballi.hazmei.tk -p 14563`  
On Xshell - `ssh <username>@bballi.hazmei.tk 14563`  

Integrated codes are all in this directory:  
`/script/Production/`

If you added new files via sftp, run the following command once you're done:  
`fixgroup`  
`fixpermission`

To test out ***main.py***, run the following command:  
`cd /script/Production/`  
`pythonenv` - This activates python virtual environment which contains all the necessary modules.  
`python3 main.py`  

To perform edit on the code, you may use ***nano***.

***Note (Software team):***  Files in the ./data/ directory are omitted. Zip up the files and share it on Google Drive instead.

---

## To Do (by 19 Oct '17)
1. ***(Software + Comms)*** Proper logging on the integrated code. Remove all lines containing prints.  
2. ***(Software)*** Read from mega_data.csv and split voltage and current data.  
3. ***(Software)*** Compute power and cumulative power.  
4. ***(Software)*** Pass prediction, power readings and other data needed as specified by ***client.py***.  
5. ***(Software)*** Debug code on ***prediction.py***. Look under error section for detail.  
6. ***(Software)*** There's 2 ***butterworth*** python code.  Remove whichever one that is not in used.  
6. ***(Comms - YZ)*** Verify ***client.py*** is compatible with evaluation server code.

---

## (Error msg) Software - prediction.py  
```
(pythonEnv) <user>@bballi:/script/Production $ python3 main.py
Using TensorFlow backend.  
[[  1.01385601e-02   6.57948013e-03   5.51248305e-02 ...,   1.02283299e+00  
   -1.26875594e-01   1.05687201e-01]  
 [  9.27557424e-03   8.92887823e-03   4.84047309e-02 ...,   1.02202797e+00  
   -1.24003701e-01   1.02102503e-01]  
 [  5.06589701e-03   7.48868287e-03   4.97749709e-02 ...,   1.01787698e+00  
   -1.24927901e-01   1.06552698e-01]  
 ...,   
 [ -1.14748406e-03   1.71443899e-04   2.64786393e-03 ...,   1.01844501e+00  
   -1.24069601e-01   1.00385197e-01]  
 [ -2.22265502e-04   1.57418102e-03   2.38105701e-03 ...,   1.01937199e+00  
   -1.22745097e-01   9.98735502e-02]  
 [  1.57550001e-03   3.07018892e-03  -2.26975698e-03 ...,   1.02117097e+00  
   -1.21325999e-01   9.49874073e-02]]  
Process Process-1:  
Traceback (most recent call last):  
  File "/usr/lib/python3.4/multiprocessing/process.py", line 254, in _bootstrap  
    self.run()  
  File "/usr/lib/python3.4/multiprocessing/process.py", line 93, in run  
    self._target(*self._args, **self._kwargs)  
  File "main.py", line 7, in prediction_process  
    prediction.main_loop()  
  File "/script/Production/prediction.py", line 113, in main_loop  
    y = model.predict(X)  
  File  "/script/Production/pythonEnv/lib/python3.4/site-packages/keras/models.py",   line 913, in predict  
    return self.model.predict(x, batch_size=batch_size, verbose=verbose)  
  File  "/script/Production/pythonEnv/lib/python3.4/site-packages/keras/engine/training.py", line 1695, in predict  
    check_batch_axis=False)  
  File  "/script/Production/pythonEnv/lib/python3.4/site-packages/keras/engine/training.py", line 144, in _standardize_input_data  
    str(array.shape))  
ValueError: Error when checking : expected lstm_1_input to have shape (None, 50, 9) but got array with shape (1, 3, 30)  
```

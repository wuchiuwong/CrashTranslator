# CrashTranslator

## 1. Introduction
Code and Data for the paper "CrashTranslator: Automatically Reproducing Mobile Application Crashes Directly from Stack Trace". For running video recordings of CrashTranslator, please go to the following link to download: [Download link](https://drive.google.com/file/d/1l-wkBorKNpyO_AISlYGvCLI8B15oP7xm/view?usp=share_link)

## 2. Details of the Datasets Used in Our Experiments

For the 46 bug reports that at least one tool can successfully reproduce:
- Number of reproducing steps to trigger the crash (donate as **Step**): average: 6.6, min: 1, max: 14
- Number of pages included in the app (donate as **Page**): average: 7.54, min: 1, max: 51
- Number of widgets in the app (donate as **Widget**): average: 51.83, min: 4, max: 260
- Number of widgets per page in the app (donate as **WPP**): min: 2, max: 17.42

The details of each report are as follows

#### Details of ReCDroids's Dataset
| **ID** | **Bug Report**  | **Step** | **Page** | **Widget** | **WPP** | **ID** | **Bug Report** | **Step** | **Page** | **Widget** | **WPP** |
|--------|-----------------|----------|----------|------------|---------|--------|----------------|----------|----------|------------|---------|
| R-1    | NewsBlur-1053   | 5        | 4        | 18         | 4.5     | R-15   | Transistor-63  | 2        | 5        | 15         | 3       |
| R-2    | Markor-194      | 4        | 5        | 68         | 13.6    | R-16   | Zom-271        | 5        | 9        | 35         | 3.89    |
| R-3    | Birthdroid-13   | 5        | 8        | 32         | 4       | R-17   | Pix-Art-125    | 3        | 5        | 22         | 4.4     |
| R-4    | Car Report-43   | 10       | 5        | 38         | 7.6     | R-18   | Pix-Art-127    | 3        | 5        | 19         | 3.8     |
| R-5    | AnyMemo-18      | 2        | 3        | 23         | 7.67    | R-19   | ScreenCam-25   | 5        | 6        | 29         | 4.83    |
| R-6    | AnyMemo-440     | 4        | 12       | 107        | 8.92    | R-20   | ownCloud-487   | 3        | 4        | 23         | 5.75    |
| R-7    | Notepad-23      | 6        | 7        | 33         | 4.71    | R-21   | OBDReader-22   | 9        | 5        | 15         | 3       |
| R-8    | Olam-2          | 2        | 1        | 4          | 4       | R-22   | Dagger-46      | 1        | 1        | 4          | 4       |
| R-9    | Olam-1          | 2        | 1        | 4          | 4       | R-23   | ODK-2086       | 3        | 51       | 260        | 5.1     |
| R-10   | FastAdapter-394 | 1        | 1        | 46         | 46      | R-24   | K-9Mail-3255   | 4        | 2        | 11         | 5.5     |
| R-11   | LibreNews-22    | 5        | 7        | 36         | 5.14    | R-25   | K-9Mail-2612   | 3        | 3        | 36         | 12      |
| R-12   | LibreNews-23    | 6        | 6        | 34         | 5.67    | R-26   | K-9Mail-2019   | 2        | 2        | 17         | 8.5     |
| R-13   | LibreNews-27    | 5        | 6        | 34         | 5.67    | R-27   | TagMo-12       | 2        | 3        | 15         | 5       |
| R-14   | SMSsync-464     | 4        | 18       | 160        | 8.89    | R-28   | FlashCards-13  | 6        | 5        | 13         | 2.6     |


#### Details of AndroR2 Dataset
| **ID** | **Bug Report** | **Step** | **Page** | **Widget** | **WPP** | **ID** | **Bug Report** | **Step** | **Page** | **Widget** | **WPP** |
|--------|----------------|----------|----------|------------|---------|--------|----------------|----------|----------|------------|---------|
| A-1    | HABPanel-25    | 5        | 6        | 12         | 2       | A-6    | K-9Mail-3255   | 4        | 2        | 11         | 5.5     |
| A-2    | Noad Player-1  | 1        | 1        | 1          | 5       | A-7    | K-9Mail-3971   | 5        | 7        | 29         | 4.14    |
| A-3    | Weather-61     | 4        | 4        | 16         | 4       | A-8    | Firefox-3932   | 5        | 8        | 63         | 7.88    |
| A-4    | Berkeley-82    | 1        | 1        | 8          | 8       | A-9    | Aegis-3932     | 14       | 15       | 101        | 6.73    |
| A-5    | andOTP-500     | 12       | 14       | 86         | 6.14    |        |                |          |          |            |         |


#### Details of CrashTranslator's Dataset
| **ID** | **Bug Report** | **Step** | **Page** | **Widget** | **WPP** | **ID** | **Bug Report** | **Step** | **Page** | **Widget** | **WPP** |
|--------|----------------|----------|----------|------------|---------|--------|----------------|----------|----------|------------|---------|
| C-1    | NewPipe-7825   | 3        | 6        | 58         | 9.67    | C-7    | WhereUGo-368   | 5        | 12       | 57         | 4.75    |
| C-2    | SDBViewer-10   | 2        | 3        | 10         | 3.33    | C-8    | GrowTracker-87 | 9        | 21       | 117        | 5.57    |
| C-3    | Anki-10584     | 2        | 7        | 72         | 10.29   | C-9    | FakeStandby-30 | 2        | 2        | 12         | 6       |
| C-5    | Shuttle-456    | 6        | 12       | 209        | 17.42   | C-10   | getodk-219     | 1        | 3        | 25         | 8.33    |
| C-6    | Anki-3370      | 6        | 12       | 60         | 5       |        |                |          |          |            |         |


## 3. Preparation Before Running

#### 3.1 Requirements
* Android emulator
* Ubuntu or Windows
* Appium Desktop Client: [Download link](https://github.com/appium/appium-desktop/releases/tag/v1.22.3-4)
* Python 3.7
  * apkutils==0.10.2
  * Appium-Python-Client==1.3.0
  * Levenshtein==0.18.1
  * lxml==4.8.0
  * opencv-python==4.5.5.64
  * openai==0.8.0  

#### 3.2 Fine-tunning GPT-3 Model
Since GPT-3 is not free, we do not provide our account (API key) and the fine-tuned model directly. You should follow the guidelines and the [official document](https://platform.openai.com/docs/guides/fine-tuning) below to fine tune the GPT-3 model on your account with the fine tuned corpus we provide.
1. Export your OpenAI API key: ```export OPENAI_API_KEY="<OPENAI_API_KEY>"```
2. Create a fine tunning task: ```openai api fine_tunes.create -t gpt3/mix_data_train.jsonl -m curie```
3. Waiting for fine-tuning to finish (20 min), and get the fine-tuned model name (e.g., ```curie:ft-personal-2023-MM-DD-hh-mm-ss```)
4. Change the API key (```openai.api_key = "****"``` in line 20) and fine-tuned model name (```model_name = "****""``` line 22) in `gpt3/gpt3_scorer.py` to your own.

## 4. How to run CrashTranslator on apps in our experiment
1. Download our data archive from Google Play and extract it to this directory: [Download link](https://drive.google.com/file/d/1NIYDcAutaQL95COjbLn8ShE3UT9ylsZ8/view?usp=share_link)
2. Launch an Android emulator and connect to it via `adb`
3. Launch the `Appium Desktop Client`
4. In the `Main` directory, there are several scripts to run CrashTranslator:
   * `run_recdroid.py`: run CrashTranslator on apps in the ReCDroid's dataset
   * `run_andror2.py`: run CrashTranslator on apps in the AndroR2 dataset
   * `run_mydata.py`: run CrashTranslator on apps in the CrashTranslator's dataset
   * To change the running app, modify the `app_idx` variable in `do_test(app_idx)`.
package org.mnemosyne;

import com.srplab.www.starcore.StarCoreFactory;
import com.srplab.www.starcore.StarCoreFactoryPath;
import com.srplab.www.starcore.StarObjectClass;
import com.srplab.www.starcore.StarServiceClass;
import com.srplab.www.starcore.StarSrvGroupClass;

import android.app.AlertDialog;
import android.app.ProgressDialog;
import android.content.DialogInterface;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;

import java.util.concurrent.Semaphore;


public class MnemosyneThread extends Thread {

    StarCoreFactory starcore;
    StarObjectClass python;
    StarObjectClass mnemosyne;
    StarObjectClass controller;
    StarObjectClass reviewController;
    MnemosyneActivity UIActivity;
    Handler mnemosyneHandler;
    Handler UIHandler;
    String basedir;

    public MnemosyneThread(MnemosyneActivity activity, Handler handler, String packageName) {
        UIActivity = activity;
        UIHandler = handler;
        basedir = "/data/data/" + packageName;
    }

    public Handler getHandler() {
        return mnemosyneHandler;
    }

    public void startMnemosyne() {

        UIHandler.post(new Runnable() {
            public void run() {
                progressDialog = new ProgressDialog(UIActivity);
                progressDialog.setCancelable(false);
                progressDialog.setProgressStyle(ProgressDialog.STYLE_SPINNER);
                progressDialog.setMessage("Initialising Mnemosyne...");
                progressDialog.setIndeterminate(true);
                progressDialog.show();
            }
        });

        StarCoreFactoryPath.StarCoreCoreLibraryPath = basedir + "/lib";
        StarCoreFactoryPath.StarCoreShareLibraryPath = basedir + "/lib";
        StarCoreFactoryPath.StarCoreOperationPath = basedir + "/files";
        starcore = StarCoreFactory.GetFactory();

        Log.d("Mnemosyne", "About to initialise starcore");

        StarSrvGroupClass SrvGroup = starcore._GetSrvGroup(0);
        StarServiceClass Service = SrvGroup._GetService("cle", "123");
        if (Service == null) {  // The service has not been initialized.
            Log.d("Mnemosyne", "Initialising starcore");
            Service = starcore._InitSimple("cle", "123", 0, 0);
            Service._CheckPassword(false);
            SrvGroup = (StarSrvGroupClass) Service._Get("_ServiceGroup");
            SrvGroup._InitRaw("python", Service);


        }
        python = Service._ImportRawContext("python", "", false, "");

        // Set up extra paths.
        python._Call("import", "sys");
        StarObjectClass pythonSys = python._GetObject("sys");
        StarObjectClass pythonPath = (StarObjectClass) pythonSys._Get("path");
        pythonPath._Call("insert", 0, basedir + "/files/python_extras_r14.zip");
        pythonPath._Call("insert", 0, basedir + "/lib");
        pythonPath._Call("insert", 0, basedir + "/files/lib-dynload");
        pythonPath._Call("insert", 0, basedir + "/files");

        Log.d("Mnemosyne", "About to start Mnemosyne");

        // Start Mnemosyne.
        SrvGroup._LoadRawModule("python", "", basedir +
                "/files/mnemosyne/cle/mnemosyne_android.py", false);

        mnemosyne = python._GetObject("mnemosyne");

        String dataDir = "/sdcard/Mnemosyne/";
        String filename = "default.db";
        python._Call("start_mnemosyne", dataDir, filename, this);

        controller = (StarObjectClass) mnemosyne._Call("controller");
        reviewController = (StarObjectClass) mnemosyne._Call("review_controller");

        Log.d("Mnemosyne", "started Mnemosyne");

        UIHandler.post(new Runnable() {
            public void run() {
                progressDialog.dismiss();
            }
        });
    }

    public void stopMnemosyne() {
        Log.d("Mnemosyne", "stopping Mnemosyne");
        python._Call("stop_mnemosyne");
        // Wait until the CLE core queue is empty.
        while (starcore._SRPDispatch(false) == true); // Empty loop, consume current queue message.
        starcore._SRPDispatch(true); // Wait a message cycle, the longest time is 10ms.
        Log.d("Mnemosyne", "Mnemosyne stopped");
        // This seems to be the best way to ensure that CLE can be restarted properly.
        android.os.Process.killProcess(android.os.Process.myPid());
    }

    @Override
    public void run() {
        Log.d("Mnemosyne", "starting running Mnemosyne thread");
        startMnemosyne();
        Looper.prepare();
        mnemosyneHandler = new Handler();
        Looper.loop();
    }

    public void setQuestionLabel(String label) {
        final String _label = label;
        UIHandler.post(new Runnable() {
            public void run() {
                UIActivity.questionLabel.setText(_label);
            }
        });
    }

    public void setQuestion(String html) {
        final String _html = html;
        UIHandler.post(new Runnable() {
            public void run() {
                UIActivity.setQuestion(_html);
            }
        });
    }

    public void setAnswer(String html) {
        final String _html = html;
        UIHandler.post(new Runnable() {
            public void run() {
                UIActivity.setAnswer(_html);
            }
        });
    }

    public void setQuestionBoxVisible(boolean isVisible) {
        final boolean _isVisible = isVisible;
        UIHandler.post(new Runnable() {
            public void run() {
                if (_isVisible) {
                    UIActivity.question.setVisibility(android.view.View.VISIBLE);
                    UIActivity.questionLabel.setVisibility(android.view.View.VISIBLE);
                }
                else {
                    UIActivity.question.setVisibility(android.view.View.GONE);
                    UIActivity.questionLabel.setVisibility(android.view.View.GONE);
                }
            }
        });
    }

    public void setAnswerBoxVisible(boolean isVisible) {
        final boolean _isVisible = isVisible;
        UIHandler.post(new Runnable() {
            public void run() {
                if (_isVisible) {
                    UIActivity.answer.setVisibility(android.view.View.VISIBLE);
                    UIActivity.answerLabel.setVisibility(android.view.View.VISIBLE);
                }
                else {
                    UIActivity.answer.setVisibility(android.view.View.GONE);
                    UIActivity.answerLabel.setVisibility(android.view.View.GONE);
                }
            }
        });
    }

    public void updateShowButton(String text, boolean isDefault, boolean isEnabled) {
        // We completely ignore isEnabled here, and rather chose to set it in
        // 'setGradesEnabled'. The reason is that breaking this up into two 'setVisibility'
        // messages causes screen flicker, probably related to ordering with respect to a
        // system-issued 'layout' call.
        // See http://stackoverflow.com/questions/3544826/android-home-screen-like-effect-flickering-problem-when-set-child-setvisibility
        final String _text = text;
        UIHandler.post(new Runnable() {
            public void run() {
                UIActivity.showAnswerButton.setText(_text);
            }
        });
    }

    public void setGradesEnabled(boolean isEnabled) {
        final boolean _isEnabled = isEnabled;
        UIHandler.post(new Runnable() {
            public void run() {
                if (_isEnabled) {
                    UIActivity.button0.setVisibility(android.view.View.VISIBLE);
                    UIActivity.button1.setVisibility(android.view.View.VISIBLE);
                    UIActivity.button2.setVisibility(android.view.View.VISIBLE);
                    UIActivity.button3.setVisibility(android.view.View.VISIBLE);
                    UIActivity.button4.setVisibility(android.view.View.VISIBLE);
                    UIActivity.button5.setVisibility(android.view.View.VISIBLE);
                    UIActivity.showAnswerButton.setVisibility(android.view.View.GONE);
                }
                else {
                    UIActivity.button0.setVisibility(android.view.View.GONE);
                    UIActivity.button1.setVisibility(android.view.View.GONE);
                    UIActivity.button2.setVisibility(android.view.View.GONE);
                    UIActivity.button3.setVisibility(android.view.View.GONE);
                    UIActivity.button4.setVisibility(android.view.View.GONE);
                    UIActivity.button5.setVisibility(android.view.View.GONE);
                    UIActivity.showAnswerButton.setVisibility(android.view.View.VISIBLE);
                }
            }
        });
    }

    public void setStatusbarText(String text) {
        final String _text = text;
        UIHandler.post(new Runnable() {
            public void run() {
                UIActivity.statusbar.setText(_text);
            }
        });
    }

    public void showInformation(String text) {
        final String _text = text;
        UIHandler.post(new Runnable() {
            public void run() {
                AlertDialog.Builder alert = new AlertDialog.Builder(UIActivity);
                alert.setMessage(_text);
                alert.setCancelable(false);
                alert.setPositiveButton("OK", new DialogInterface.OnClickListener() {
                    public void onClick(DialogInterface dialog, int whichButton) {
                        return;
                    }
                });
                alert.show();
            }
        });
    }

    int result = -1;
    Semaphore semaphore = new Semaphore(0);

    public int showQuestion(String text, String option0, String option1, String option2) {
        final String _text = text;
        final String _option0 = option0;
        final String _option1 = option1;
        final String _option2 = option2;

        UIHandler.post(new Runnable() {
            public void run() {
                AlertDialog.Builder alert = new AlertDialog.Builder(UIActivity);
                alert.setMessage(_text);
                alert.setCancelable(false);
                alert.setPositiveButton(_option0, new DialogInterface.OnClickListener() {
                    public void onClick(DialogInterface dialog, int whichButton) {
                        result = 0;
                        semaphore.release();
                    }
                });
                alert.setNeutralButton(_option1, new DialogInterface.OnClickListener() {
                    public void onClick(DialogInterface dialog, int whichButton) {
                        result = 1;
                        semaphore.release();
                    }
                });
                alert.setNegativeButton(_option2, new DialogInterface.OnClickListener() {
                    public void onClick(DialogInterface dialog, int whichButton) {
                        result = 2;
                        semaphore.release();
                    }
                });
                alert.show();
            }
        });

        try {
            semaphore.acquire();
        }
        catch (InterruptedException e) {
        }
        return result;
    }

    public void showSyncDialog() {
        UIHandler.post(new Runnable() {
            public void run() {
                //Intent startNewActivityOpen = new Intent(this, SyncActivity.class);
                //startActivityForResult(startNewActivityOpen, 0);
                AlertDialog.Builder alert = new AlertDialog.Builder(UIActivity);
                alert.setMessage("Click to sync");
                alert.setCancelable(false);
                alert.setPositiveButton("Sync", new DialogInterface.OnClickListener() {
                    public void onClick(DialogInterface dialog, int whichButton) {
                        result = 0;
                        semaphore.release();
                    }
                });
                alert.show();
            }
        });

        try {
            semaphore.acquire();
        }
        catch (InterruptedException e) {
        }

        controller._Call("sync", "dyndns.org", 8512, "", "");
    }

    private ProgressDialog progressDialog;
    private int progressValue = 0;
    private String progressText = "";

    public void setProgressText(String text) {
        progressText = text;
        final String _text = text;
        UIHandler.post(new Runnable() {
            public void run() {
                if (progressDialog != null) {
                    progressDialog.dismiss();
                }
                progressDialog = new ProgressDialog(UIActivity);
                progressDialog.setCancelable(false);
                progressDialog.setMessage(_text);
                progressDialog.setProgress(0);
                progressValue = 0;
                progressDialog.show();
            }
        });
    }

    public void setProgressRange(int maximum) {
        final int _maximum = maximum;
        UIHandler.post(new Runnable() {
            public void run() {
                // Android doesn't like changing style on the fly, so we recreate the
                // progress dialog.
                if (progressDialog != null) {
                    progressDialog.dismiss();
                }
                progressDialog = new ProgressDialog(UIActivity);
                progressDialog.setCancelable(false);
                progressDialog.setMessage(progressText);
                progressDialog.setProgress(0);
                progressValue = 0;
                progressDialog.setProgressStyle(ProgressDialog.STYLE_HORIZONTAL);
                progressDialog.setMax(_maximum);
                progressDialog.show();
            }
        });
    }

    public void setProgressValue(int value) {
        final int _value = value;
        UIHandler.post(new Runnable() {
            public void run() {
                if (_value >= progressDialog.getMax()) {
                    closeProgress();
                    return;
                }
                progressValue = _value;
                progressDialog.setProgress(progressValue);
            }
        });
    }

    public void closeProgress() {
        UIHandler.post(new Runnable() {
            public void run() {
                if (progressDialog != null) {
                    progressDialog.dismiss();
                }
            }
        });
    }

}
package com.mooney.safetynetexploration;

import android.os.AsyncTask;
import android.support.annotation.NonNull;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;

import com.google.android.gms.safetynet.SafetyNet;
import com.google.android.gms.safetynet.SafetyNetApi;
import com.google.android.gms.safetynet.SafetyNetClient;
import com.google.android.gms.tasks.OnCompleteListener;
import com.google.android.gms.tasks.OnFailureListener;
import com.google.android.gms.tasks.Task;

import java.io.IOException;
import java.security.SecureRandom;

public class MainActivity extends AppCompatActivity {
    Button safetyNetButton;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);


        safetyNetButton = (Button) findViewById(R.id.button);
        safetyNetButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                new GetAndPostSafetyNetAssertionTask().execute();
            }
        });
    }

    private class GetAndPostSafetyNetAssertionTask extends AsyncTask<Void, Void, Void> {

        @Override
        protected Void doInBackground(Void... voids) {
            SecureRandom random = new SecureRandom();
            byte nonce[] = new byte[20];
            random.nextBytes(nonce);

            final SillyFlaskThingClient flaskThingClient = new SillyFlaskThingClient();
            SafetyNetClient safetyNetClient = SafetyNet.getClient(getApplicationContext());
            safetyNetClient.attest(nonce, getApplicationContext().getString(R.string.safetynet_api_key)).addOnCompleteListener(new OnCompleteListener<SafetyNetApi.AttestationResponse>() {
                @Override
                public void onComplete(@NonNull Task<SafetyNetApi.AttestationResponse> task) {
                    String attResponse = task.getResult().getJwsResult();
                    try {
                        flaskThingClient.submitSafetyNetJWS(attResponse);
                    } catch (IOException e) {
                        e.printStackTrace();
                    }
                }
            }).addOnFailureListener(new OnFailureListener() {
                @Override
                public void onFailure(@NonNull Exception e) {
                    // :(
                }
            });

            return null;
        }
    }
}

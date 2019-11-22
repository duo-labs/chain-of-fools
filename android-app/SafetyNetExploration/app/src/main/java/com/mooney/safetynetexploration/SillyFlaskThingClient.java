package com.mooney.safetynetexploration;

import java.io.IOException;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;
import retrofit2.Retrofit;
import retrofit2.converter.gson.GsonConverterFactory;

public class SillyFlaskThingClient {
    private Retrofit retrofit;
    private SillyFlaskThingService flaskThingService;

    public SillyFlaskThingClient() {
        Retrofit retrofit = new Retrofit.Builder()
                .baseUrl("http://192.168.0.100")
                .addConverterFactory(GsonConverterFactory.create())
                .build();
        SillyFlaskThingService flaskThingService = retrofit.create(SillyFlaskThingService.class);

        this.retrofit = retrofit;
        this.flaskThingService = flaskThingService;
    }

    public void submitSafetyNetJWS(String jws) throws IOException {
        flaskThingService.submitSafetyNetJWS(jws).enqueue(new Callback<String>() {
            @Override
            public void onResponse(Call<String> call, Response<String> response) {

            }

            @Override
            public void onFailure(Call<String> call, Throwable t) {

            }
        });
    }
}

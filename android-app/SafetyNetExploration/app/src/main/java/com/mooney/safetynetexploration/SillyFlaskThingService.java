package com.mooney.safetynetexploration;

import retrofit2.Call;
import retrofit2.http.Field;
import retrofit2.http.FormUrlEncoded;
import retrofit2.http.POST;

public interface SillyFlaskThingService {
    @FormUrlEncoded
    @POST("safetynet/validate")
    Call<String> submitSafetyNetJWS(@Field("jws") String jws);
}

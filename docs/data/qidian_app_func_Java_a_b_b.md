```c
jobject __fastcall Java_a_b_b(
    JNIEnv *env,
    jobject clazz,
    jlong bookIdLong,
    jlong chapterIdLong,
    jbyteArray dataArray,
    jlong userIdLong,
    jstring imei)
{
  char *bookIdCStr; // x19
  char *chapterIdCStr; // x21
  const char *userIdCStr; // x23
  _OWORD *secBuffer1; // x27
  _OWORD *secBuffer2; // x28
  _OWORD *sha2KeyBufArea; // x0
  const char *sha2KeyCStr; // x25
  jclass clsAB_1; // x0
  void *clsAB_ref1; // x26
  const char *imeiCStr; // x24
  char *ptrAfterFirstConcat; // x24
  char *ptrAfterChapterConcat; // x0
  struct _jmethodID *mid_s; // x24
  jobject jSha1Key1; // x26
  const char *sha1Key1CStr; // x24
  jstring jSec2Str; // x24
  struct _jmethodID *mid_m; // x26
  jstring jUserIdJStr; // x0
  void *clsAB_ref2; // x1
  jobject jSha1Key2; // x22
  const char *sha1Key2CStr; // x24
  jstring jSha2KeyJStr; // x26
  struct _jmethodID *mid_d; // x22
  jobject intermediateData1; // x27
  jobject finalData; // x22
  jstring jSec1Str; // [xsp+0h] [xbp-30h]
  jstring jSha1Key1FinalStr; // [xsp+0h] [xbp-30h]
  const char *imeiCStrRef; // [xsp+8h] [xbp-28h]
  jclass clsAB_3; // [xsp+10h] [xbp-20h]
  jclass clsAB_2; // [xsp+18h] [xbp-18h]
  void *jUserIdJStrRef; // [xsp+18h] [xbp-18h]

  bookIdCStr = (char *)malloc(0x40u);
  *(_OWORD *)bookIdCStr = 0u;
  *((_OWORD *)bookIdCStr + 1) = 0u;
  *((_OWORD *)bookIdCStr + 2) = 0u;
  *((_OWORD *)bookIdCStr + 3) = 0u;
  sub_1230((__int64)bookIdCStr, 64LL, (__int64)"%lld", bookIdLong);

  chapterIdCStr = (char *)malloc(0x40u);
  *(_OWORD *)chapterIdCStr = 0u;
  *((_OWORD *)chapterIdCStr + 1) = 0u;
  *((_OWORD *)chapterIdCStr + 2) = 0u;
  *((_OWORD *)chapterIdCStr + 3) = 0u;
  sub_1230((__int64)chapterIdCStr, 64LL, (__int64)"%lld", chapterIdLong);

  userIdCStr = (const char *)malloc(0x40u);
  *(_OWORD *)userIdCStr = 0u;
  *((_OWORD *)userIdCStr + 1) = 0u;
  *((_OWORD *)userIdCStr + 2) = 0u;
  *((_OWORD *)userIdCStr + 3) = 0u;
  sub_1230((__int64)userIdCStr, 64LL, (__int64)"%lld", userIdLong);

  secBuffer1 = malloc(0xFFu);
  *secBuffer1 = 0u;
  secBuffer1[1] = 0u;
  secBuffer1[2] = 0u;
  secBuffer1[3] = 0u;
  secBuffer1[4] = 0u;
  secBuffer1[5] = 0u;
  secBuffer1[6] = 0u;
  secBuffer1[7] = 0u;
  secBuffer1[8] = 0u;
  secBuffer1[9] = 0u;
  secBuffer1[10] = 0u;
  secBuffer1[11] = 0u;
  secBuffer1[12] = 0u;
  secBuffer1[13] = 0u;
  secBuffer1[14] = 0u;
  *(_OWORD *)((char *)secBuffer1 + 239) = 0u;

  secBuffer2 = malloc(0xFFu);
  *secBuffer2 = 0u;
  secBuffer2[1] = 0u;
  secBuffer2[2] = 0u;
  secBuffer2[3] = 0u;
  secBuffer2[4] = 0u;
  secBuffer2[5] = 0u;
  secBuffer2[6] = 0u;
  secBuffer2[7] = 0u;
  secBuffer2[8] = 0u;
  secBuffer2[9] = 0u;
  secBuffer2[10] = 0u;
  secBuffer2[11] = 0u;
  secBuffer2[12] = 0u;
  secBuffer2[13] = 0u;
  secBuffer2[14] = 0u;
  *(_OWORD *)((char *)secBuffer2 + 239) = 0u;

  sha2KeyBufArea = malloc(0xFFu);
  *sha2KeyBufArea = 0u;
  sha2KeyBufArea[1] = 0u;
  sha2KeyBufArea[2] = 0u;
  sha2KeyBufArea[3] = 0u;
  sha2KeyBufArea[4] = 0u;
  sha2KeyBufArea[5] = 0u;
  sha2KeyBufArea[6] = 0u;
  sha2KeyBufArea[7] = 0u;
  sha2KeyBufArea[8] = 0u;
  sha2KeyBufArea[9] = 0u;
  sha2KeyBufArea[10] = 0u;
  sha2KeyBufArea[11] = 0u;
  sha2KeyBufArea[12] = 0u;
  sha2KeyBufArea[13] = 0u;
  sha2KeyBufArea[14] = 0u;
  *(_OWORD *)((char *)sha2KeyBufArea + 239) = 0u;

  sha2KeyCStr = (const char *)sha2KeyBufArea;

  clsAB_1 = (*env)->FindClass(env, "a/b");
  if ( !clsAB_1 )
    return 0LL;
  clsAB_ref1 = clsAB_1;

  clsAB_2 = (*env)->FindClass(env, "a/b");
  if ( !clsAB_2 )
    return 0LL;

  clsAB_3 = (*env)->FindClass(env, "a/b");
  if ( !clsAB_3 )
    return 0LL;

  __android_log_print(3, "QDReader_Jni", "JNI:0");
  imeiCStr = (*env)->GetStringUTFChars(env, imei, 0LL);
  __android_log_print(
    3,
    "QDReader_Jni",
    "bookid: %s,chapterid: %s,userid: %s,imei: %s",
    bookIdCStr,
    chapterIdCStr,
    userIdCStr,
    imeiCStr);
  __android_log_print(3, "QDReader_Jni", "JNI:1");

  __strcpy_chk(secBuffer1, userIdCStr, 255LL);
  imeiCStrRef = imeiCStr;
  ptrAfterFirstConcat = (char *)__strcat_chk(secBuffer1, imeiCStr, 255LL);
  ptrAfterChapterConcat = strcat(ptrAfterFirstConcat, chapterIdCStr);
  strcpy(&ptrAfterFirstConcat[strlen(ptrAfterChapterConcat)], "2EEE1433A152E84B3756301D8FA3E69A");
  __android_log_print(3, "QDReader_Jni", "JNI:2");

  jSec1Str = (*env)->NewStringUTF(env, secBuffer1);
  __android_log_print(3, "QDReader_Jni", "JNI:3");

  mid_s = (*env)->GetStaticMethodID(env, clsAB_ref1, "s", "(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;");
  __android_log_print(3, "QDReader_Jni", "JNI:4");
  if ( !mid_s )
    return 0LL;
  __android_log_print(3, "QDReader_Jni", "sha1id:%d", mid_s);
  __android_log_print(3, "QDReader_Jni", "JNI:5");

  jSha1Key1 = (*env)->CallStaticObjectMethod(env, clsAB_ref1, mid_s, imei, jSec1Str);
  (*env)->ReleaseStringUTFChars(env, jSec1Str, (const char *)secBuffer1);
  __android_log_print(3, "QDReader_Jni", "JNI:6");

  sha1Key1CStr = (*env)->GetStringUTFChars(env, jSha1Key1, 0LL);
  __android_log_print(3, "QDReader_Jni", "sha1key1 = %s", sha1Key1CStr);
  __android_log_print(3, "QDReader_Jni", "JNI:7");

  if ( strlen(sha1Key1CStr) >= 0x18uLL )
  {
    memset(gShaKeyBuf, 0, sizeof(gShaKeyBuf));
    strncpy(gShaKeyBuf, sha1Key1CStr, 0x18u);
  }
  __android_log_print(3, "QDReader_Jni", "JNI:8 sha1key2:%s sha1key1:%s", gShaKeyBuf, sha1Key1CStr);
  (*env)->ReleaseStringUTFChars(env, jSha1Key1, sha1Key1CStr);

  jSha1Key1FinalStr = (*env)->NewStringUTF(env, gShaKeyBuf);
  __android_log_print(3, "QDReader_Jni", "JNI:9");

  __strcpy_chk(secBuffer2, gShaKeyBuf, 255LL);
  __strcat_chk(secBuffer2, imeiCStrRef, 255LL);
  __android_log_print(3, "QDReader_Jni", "JNI:10");

  jSec2Str = (*env)->NewStringUTF(env, secBuffer2);
  __android_log_print(3, "QDReader_Jni", "JNI:11");

  mid_m = (*env)->GetStaticMethodID(env, clsAB_2, "m", "(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;");
  __android_log_print(3, "QDReader_Jni", "JNI:12");
  if ( !mid_m )
    return 0LL;
  __android_log_print(3, "QDReader_Jni", "JNI:13");

  jUserIdJStr = (*env)->NewStringUTF(env, userIdCStr);
  clsAB_ref2 = clsAB_2;
  jUserIdJStrRef = jUserIdJStr;
  jSha1Key2 = (*env)->CallStaticObjectMethod(env, clsAB_ref2, mid_m);
  (*env)->ReleaseStringUTFChars(env, jSec2Str, (const char *)secBuffer2);
  __android_log_print(3, "QDReader_Jni", "JNI:14");

  sha1Key2CStr = (*env)->GetStringUTFChars(env, jSha1Key2, 0LL);
  __android_log_print(3, "QDReader_Jni", "JNI:15");

  if ( strlen(sha1Key2CStr) < 0x19uLL )
  {
    __strcpy_chk(sha2KeyCStr, sha1Key2CStr, 255LL);
  }
  else
  {
    sha2KeyCStr = gShaKeyBuf;
    memset(gShaKeyBuf, 0, sizeof(gShaKeyBuf));
    strncpy(gShaKeyBuf, sha1Key2CStr, 0x18u);
  }
  (*env)->ReleaseStringUTFChars(env, jSha1Key2, sha1Key2CStr);
  __android_log_print(3, "QDReader_Jni", "JNI:16");

  jSha2KeyJStr = (*env)->NewStringUTF(env, sha2KeyCStr);
  __android_log_print(3, "QDReader_Jni", "JNI:17");

  mid_d = (*env)->GetStaticMethodID(env, clsAB_3, "d", "([BLjava/lang/String;)[B");
  __android_log_print(3, "QDReader_Jni", "JNI:18");
  if ( !mid_d )
    return 0LL;
  __android_log_print(3, "QDReader_Jni", "JNI:19");

  intermediateData1 = (*env)->CallStaticObjectMethod(env, clsAB_3, mid_d, dataArray, jSha2KeyJStr);
  __android_log_print(3, "QDReader_Jni", "JNI:20");

  finalData = (*env)->CallStaticObjectMethod(env, clsAB_3, mid_d, intermediateData1, jSha1Key1FinalStr);
  __android_log_print(3, "QDReader_Jni", "JNI:21");

  (*env)->ReleaseStringUTFChars(env, imei, imeiCStrRef);
  __android_log_print(3, "QDReader_Jni", "JNI:22 %s", gShaKeyBuf);
  __android_log_print(3, "QDReader_Jni", "JNI:23");

  (*env)->ReleaseStringUTFChars(env, jSha2KeyJStr, sha2KeyCStr);
  __android_log_print(3, "QDReader_Jni", "JNI:24");

  (*env)->ReleaseStringUTFChars(env, jUserIdJStrRef, userIdCStr);
  __android_log_print(3, "QDReader_Jni", "JNI:25");

  free(bookIdCStr);
  __android_log_print(3, "QDReader_Jni", "JNI:26");

  free(chapterIdCStr);
  __android_log_print(3, "QDReader_Jni", "JNI:27");

  return finalData;
}
```

`package a`:

```java
package a;

import android.content.Context;
import android.util.Base64;
import bf.cihai;
import com.qidian.QDReader.autotracker.bean.AutoTrackerItem;
import com.qidian.common.lib.Logger;
import com.qidian.common.lib.util.q0;
import java.security.NoSuchAlgorithmException;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

public class b {
    private static final String CHARSET_ASCII = "ascii";
    private static final String MAC_SHA1_NAME = "HmacSHA1";

    static {
        try {
            System.loadLibrary("load-jni");
        } catch (Exception e10) {
            e10.printStackTrace();
        } catch (UnsatisfiedLinkError e11) {
            e11.printStackTrace();
        }
    }

    public static native byte[] b(long j10, long j11, byte[] bArr, long j12, String str);

    public static native void c(Context context);

    public static byte[] d(byte[] bArr, String str) {
        try {
            return cihai.search(bArr, str);
        } catch (Exception e10) {
            Logger.exception(e10);
            return null;
        }
    }

    private static String encryptToSHA1(String str, String str2) throws Exception {
        SecretKeySpec secretKeySpec = new SecretKeySpec(str.getBytes(CHARSET_ASCII), MAC_SHA1_NAME);
        Mac mac = Mac.getInstance(MAC_SHA1_NAME);
        mac.init(secretKeySpec);
        return new String(Base64.encode(mac.doFinal(str2.getBytes(CHARSET_ASCII)), 0));
    }

    public static String m(String str, String str2) {
        String str3;
        try {
            str3 = bf.a.judian(str, str2);
        } catch (NoSuchAlgorithmException e10) {
            e = e10;
            str3 = null;
        }
        try {
            if (str3.length() != 24) {
                d5.cihai.p(new AutoTrackerItem.Builder().setPn("OKR_b_m").setEx1(String.valueOf(str3.length())).setEx2(str + "/" + str2 + "/" + str3).buildCol());
            }
        } catch (NoSuchAlgorithmException e11) {
            e = e11;
            Logger.exception(e);
            return str3;
        }
        return str3;
    }

    public static String s(String str, String str2) {
        String str3;
        try {
            str3 = encryptToSHA1(str, str2);
            try {
                if (str3.length() >= 24) {
                    return str3;
                }
                d5.cihai.p(new AutoTrackerItem.Builder().setPn("OKR_b_s").setEx1(String.valueOf(str3.length())).setEx2(str + "/" + str2 + "/" + str3).buildCol());
                return q0.m(str3, 24, (char) 0);
            } catch (Exception e10) {
                e = e10;
                Logger.exception(e);
                return str3;
            }
        } catch (Exception e11) {
            e = e11;
            str3 = null;
        }
    }
}
```

`q0.m`:

```java
public static String m(String str, int i10, char c10) {
    StringBuilder sb = new StringBuilder();
    sb.append(str);
    int length = i10 - str.length();
    for (int i11 = 0; i11 < length; i11++) {
        sb.append(c10);
    }
    return sb.toString();
}
```

`package bf`:

```java
package bf;

import com.qidian.QDReader.qmethod.pandoraex.monitor.c;
import com.qidian.common.lib.Logger;
import java.nio.charset.StandardCharsets;
import javax.crypto.Cipher;
import javax.crypto.spec.IvParameterSpec;
import javax.crypto.spec.SecretKeySpec;

public class cihai {

    /* renamed from: search, reason: collision with root package name */
    private static final String f1806search = "bf.cihai";

    public static String cihai(String str, String str2) throws Exception {
        IvParameterSpec ivParameterSpec = new IvParameterSpec(new byte[8]);
        byte[] bytes = str2.getBytes("UTF-8");
        if (bytes.length == 16) {
            byte[] bArr = new byte[24];
            System.arraycopy(bytes, 0, bArr, 0, 16);
            System.arraycopy(bytes, 0, bArr, 16, 8);
            bytes = bArr;
        }
        SecretKeySpec secretKeySpec = new SecretKeySpec(bytes, "DESede");
        Cipher cipher = Cipher.getInstance("DESede/CBC/PKCS5Padding");
        if (cipher == null) {
            return "";
        }
        cipher.init(1, secretKeySpec, ivParameterSpec);
        return search.judian(c.search(cipher, str.getBytes()));
    }

    public static String judian(byte[] bArr, String str) throws Exception {
        IvParameterSpec ivParameterSpec = new IvParameterSpec("01234567".getBytes(StandardCharsets.UTF_8));
        byte[] bytes = str.getBytes("UTF-8");
        if (bytes.length == 16) {
            byte[] bArr2 = new byte[24];
            System.arraycopy(bytes, 0, bArr2, 0, 16);
            System.arraycopy(bytes, 0, bArr2, 16, 8);
            bytes = bArr2;
        }
        SecretKeySpec secretKeySpec = new SecretKeySpec(bytes, "DESede");
        Cipher cipher = Cipher.getInstance("DESede/CBC/PKCS5Padding");
        if (cipher == null) {
            return "";
        }
        cipher.init(1, secretKeySpec, ivParameterSpec);
        return search.judian(c.search(cipher, bArr));
    }

    public static byte[] search(byte[] bArr, String str) throws Exception {
        if (bArr != null && str != null) {
            IvParameterSpec ivParameterSpec = new IvParameterSpec(new byte[8]);
            byte[] bytes = str.getBytes("UTF-8");
            if (bytes != null && bytes.length >= 1) {
                if (bytes.length == 16) {
                    byte[] bArr2 = new byte[24];
                    System.arraycopy(bytes, 0, bArr2, 0, 16);
                    System.arraycopy(bytes, 0, bArr2, 16, 8);
                    bytes = bArr2;
                }
                Cipher cipher = Cipher.getInstance("DESede/CBC/PKCS5Padding");
                if (cipher == null) {
                    Logger.e(f1806search, "cipher is null");
                    return null;
                }
                cipher.init(2, new SecretKeySpec(bytes, "DESede"), ivParameterSpec);
                try {
                    return c.search(cipher, bArr);
                } catch (Exception e10) {
                    e10.printStackTrace();
                    int length = bArr.length;
                    Logger.e(f1806search, "decryptDES失败：" + str + "," + length);
                    return null;
                }
            }
            Logger.e(f1806search, "keyBytes is illegal");
        }
        return null;
    }
}
```

```java
package bf;

import com.tencent.qcloud.core.util.IOUtils;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;

public class a {

    /* renamed from: search, reason: collision with root package name */
    private static char[] f1805search = {'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '+', IOUtils.DIR_SEPARATOR_UNIX};

    public static String a(String str) throws Exception {
        byte[] digest = MessageDigest.getInstance("MD5").digest(str.getBytes("UTF-8"));
        StringBuilder sb = new StringBuilder(digest.length * 2);
        for (byte b10 : digest) {
            int i10 = b10 & 255;
            if (i10 < 16) {
                sb.append("0");
            }
            sb.append(Integer.toHexString(i10));
        }
        return sb.toString();
    }

    private static byte[] b(byte[] bArr) throws NoSuchAlgorithmException {
        MessageDigest messageDigest = MessageDigest.getInstance("MD5");
        messageDigest.update(bArr);
        return messageDigest.digest();
    }

    private static byte[] cihai(byte[] bArr, byte[] bArr2) throws NoSuchAlgorithmException {
        byte[] bArr3 = new byte[64];
        byte[] bArr4 = new byte[64];
        for (int i10 = 0; i10 < 64; i10++) {
            bArr3[i10] = 54;
            bArr4[i10] = 92;
        }
        byte[] bArr5 = new byte[64];
        if (bArr.length > 64) {
            bArr = b(bArr);
        }
        for (int i11 = 0; i11 < bArr.length; i11++) {
            bArr5[i11] = bArr[i11];
        }
        if (bArr.length < 64) {
            for (int length = bArr.length; length < 64; length++) {
                bArr5[length] = 0;
            }
        }
        byte[] bArr6 = new byte[64];
        for (int i12 = 0; i12 < 64; i12++) {
            bArr6[i12] = (byte) (bArr5[i12] ^ bArr3[i12]);
        }
        byte[] bArr7 = new byte[bArr2.length + 64];
        for (int i13 = 0; i13 < 64; i13++) {
            bArr7[i13] = bArr6[i13];
        }
        for (int i14 = 0; i14 < bArr2.length; i14++) {
            bArr7[i14 + 64] = bArr2[i14];
        }
        byte[] b10 = b(bArr7);
        byte[] bArr8 = new byte[64];
        for (int i15 = 0; i15 < 64; i15++) {
            bArr8[i15] = (byte) (bArr5[i15] ^ bArr4[i15]);
        }
        byte[] bArr9 = new byte[b10.length + 64];
        for (int i16 = 0; i16 < 64; i16++) {
            bArr9[i16] = bArr8[i16];
        }
        for (int i17 = 0; i17 < b10.length; i17++) {
            bArr9[i17 + 64] = b10[i17];
        }
        return b(bArr9);
    }

    public static String judian(String str, String str2) throws NoSuchAlgorithmException {
        return search(cihai(str.getBytes(), str2.getBytes()));
    }

    public static String search(byte[] bArr) {
        StringBuffer stringBuffer = new StringBuffer();
        int length = bArr.length;
        int i10 = 0;
        while (true) {
            if (i10 >= length) {
                break;
            }
            int i11 = i10 + 1;
            int i12 = bArr[i10] & 255;
            if (i11 == length) {
                stringBuffer.append(f1805search[i12 >>> 2]);
                stringBuffer.append(f1805search[(i12 & 3) << 4]);
                stringBuffer.append("==");
                break;
            }
            int i13 = i11 + 1;
            int i14 = bArr[i11] & 255;
            if (i13 == length) {
                stringBuffer.append(f1805search[i12 >>> 2]);
                stringBuffer.append(f1805search[((i12 & 3) << 4) | ((i14 & 240) >>> 4)]);
                stringBuffer.append(f1805search[(i14 & 15) << 2]);
                stringBuffer.append("=");
                break;
            }
            int i15 = i13 + 1;
            int i16 = bArr[i13] & 255;
            stringBuffer.append(f1805search[i12 >>> 2]);
            stringBuffer.append(f1805search[((i12 & 3) << 4) | ((i14 & 240) >>> 4)]);
            stringBuffer.append(f1805search[((i14 & 15) << 2) | ((i16 & 192) >>> 6)]);
            stringBuffer.append(f1805search[i16 & 63]);
            i10 = i15;
        }
        return stringBuffer.toString();
    }
}
```

`package com.qidian.QDReader.qmethod.pandoraex.monitor`:

```java
package com.qidian.QDReader.qmethod.pandoraex.monitor;

import j$.util.concurrent.ConcurrentHashMap;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import javax.crypto.BadPaddingException;
import javax.crypto.Cipher;
import javax.crypto.IllegalBlockSizeException;

public class c {

    /* renamed from: search, reason: collision with root package name */
    private static ConcurrentHashMap<String, byte[]> f26010search = new ConcurrentHashMap<>();

    public static void a(byte[] bArr, byte[] bArr2) {
        f26010search.put(judian(bArr), bArr2);
    }

    public static byte[] cihai(byte[] bArr) {
        byte[] bArr2 = null;
        while (bArr != null) {
            bArr = f26010search.get(judian(bArr));
            if (bArr != null) {
                bArr2 = bArr;
            }
        }
        return bArr2;
    }

    public static String judian(byte[] bArr) {
        try {
            byte[] digest = MessageDigest.getInstance("MD5").digest(bArr);
            StringBuilder sb = new StringBuilder();
            for (byte b10 : digest) {
                sb.append(String.format("%02x", Byte.valueOf(b10)));
            }
            return sb.toString();
        } catch (NoSuchAlgorithmException e10) {
            throw new RuntimeException("MD5 algorithm is not available", e10);
        }
    }

    public static byte[] search(Cipher cipher, byte[] bArr) throws IllegalBlockSizeException, BadPaddingException {
        byte[] doFinal = cipher.doFinal(bArr);
        if (com.qidian.QDReader.qmethod.pandoraex.core.ext.netcap.g.a()) {
            a(doFinal, bArr);
        }
        return doFinal;
    }
}
```

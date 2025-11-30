```java
public static ChapterContentItem H(long j10, ChapterItem chapterItem) throws Throwable {
    long j11;
    byte[] bArr;
    JSONObject jSONObject;
    String strEncode;
    long jCurrentTimeMillis = System.currentTimeMillis();
    ChapterContentItem chapterContentItem = new ChapterContentItem();
    String strF = F(j10, chapterItem);
    File file = new File(strF);
    d dVarW = W(file, chapterItem);
    if (dVarW == null) {
        h0("OKR_chapter_vip_null", String.valueOf(j10), String.valueOf(chapterItem.ChapterId), String.valueOf(-20076), "chapter data is null", "");
        chapterContentItem.setErrorCode(-20076);
        return chapterContentItem;
    }
    byte[][] bArr2 = dVarW.f18975search;
    if (bArr2 == null || bArr2.length < 2) {
        g0("OKR_chapter_vip_empty", j10, chapterItem, dVarW);
        chapterContentItem.setErrorCode(-20076);
        return chapterContentItem;
    }
    byte[] bArr3 = bArr2[0];
    byte[] bArr4 = bArr2[1];
    byte[] bArr5 = bArr2[2];
    byte[] bArr6 = bArr2[3];
    byte[] bArr7 = bArr2[4];
    long J = J(bArr3);
    if (J != 0 && J < vi.judian.e().f()) {
        chapterContentItem.setErrorCode(-20067);
        return chapterContentItem;
    }
    byte[] bArrX = x(bArr4, j10, chapterItem.ChapterId);
    if (bArrX == null) {
        if (file.exists()) {
            String strM = com.qidian.common.lib.util.m.m(file);
            strEncode = !TextUtils.isEmpty(strM) ? URLEncoder.encode(strM) : "";
        } else {
            strEncode = "file_not_found_" + strF;
        }
        d5.cihai.p(new AutoTrackerItem.Builder().setPn("OKR_chapter_vip_error").setDt("1103").setPdid(String.valueOf(j10)).setDid(String.valueOf(chapterItem.ChapterId)).setPdt(String.valueOf(strEncode.length())).setEx1(String.valueOf(QDUserManager.getInstance().k())).setEx2(QDUserManager.getInstance().s()).setEx3(QDUserManager.getInstance().t()).setEx4(we.d.I().d()).setEx5(strEncode).setAbtest("true").setKeyword("v2").buildCol());
        chapterContentItem.setErrorCode(-20068);
        return chapterContentItem;
    }
    String strW = w(bArrX);
    JSONObject jSONObjectQ = Q(strW);
    if (jSONObjectQ != null) {
        strW = jSONObjectQ.optString("content");
        int iOptInt = jSONObjectQ.optInt("type");
        int iOptInt2 = jSONObjectQ.optInt("code");
        String strOptString = jSONObjectQ.optString("msg");
        j11 = jCurrentTimeMillis;
        bArr = bArr7;
        e0.f18516search.a(j10, chapterItem.ChapterId, new e0.search(jSONObjectQ.optLong("idExpire"), jSONObjectQ.optInt("wt")));
        if (iOptInt2 != 0) {
            chapterContentItem.setErrorCode(iOptInt2);
            chapterContentItem.setErrorMessage(strOptString);
            return chapterContentItem;
        }
        if (TextUtils.isEmpty(strW)) {
            chapterContentItem.setErrorCode(-20088);
            return chapterContentItem;
        }
        String str = j10 + "_" + chapterItem.ChapterId;
        if (iOptInt == LockType.FOCK.getType()) {
            String strValueOf = String.valueOf(chapterItem.ChapterId);
            FockUtil fockUtil = FockUtil.INSTANCE;
            boolean zIsHasKey = fockUtil.isHasKey();
            Fock.FockResult fockResultUnlock = fockUtil.unlock(strW, strValueOf, str);
            if (fockResultUnlock.status == Fock.FockResult.STATUS_EMPTY_USER_KEY) {
                Fock.setup(we.d.X());
                fockResultUnlock = fockUtil.unlock(strW, strValueOf, str);
            }
            Fock.FockResult fockResult = fockResultUnlock;
            Logger.e("FockUtil: chapter_id:" + chapterItem.ChapterId + ",result:" + fockResult.status);
            if (fockResult.status != 0) {
                fockUtil.report(j10, chapterItem, fockResult, zIsHasKey);
            }
            int i10 = fockResult.status;
            if (i10 != 0) {
                if (i10 == -2) {
                    chapterContentItem.setErrorCode(-20079);
                    d5.cihai.p(new AutoTrackerItem.Builder().setPn("OKR_LoadChapterFailed_qimeiChanged").setEx1(String.valueOf(j10)).setEx2(String.valueOf(chapterItem.ChapterId)).buildCol());
                    return chapterContentItem;
                }
                if (i10 == Fock.FockResult.STATUS_EMPTY_USER_KEY) {
                    chapterContentItem.setErrorCode(-20082);
                    return chapterContentItem;
                }
                chapterContentItem.setErrorCode(-20080);
                return chapterContentItem;
            }
            strW = new String(fockResult.data, StandardCharsets.UTF_8);
        } else if (iOptInt != LockType.DEFAULT.getType()) {
            chapterContentItem.setErrorCode(-20081);
            return chapterContentItem;
        }
    } else {
        j11 = jCurrentTimeMillis;
        bArr = bArr7;
    }
    String str2 = strW;
    ArrayList<BlockInfo> arrayList = null;
    if (bArr5 != null) {
        try {
            jSONObject = new JSONObject(w(bArr5));
        } catch (Exception e10) {
            e10.printStackTrace();
        }
    } else {
        jSONObject = null;
    }
    chapterContentItem.setChapterContent(str2);
    chapterContentItem.setOriginalChapterContent(str2);
    chapterContentItem.setAuthorContent(jSONObject);
    if (bArr != null) {
        try {
            String strW2 = w(bArr);
            if (strW2 != null) {
                arrayList = (ArrayList) new Gson().j(strW2, new b().getType());
            }
        } catch (Exception e11) {
            e11.printStackTrace();
        }
        chapterContentItem.setBlockInfos(arrayList);
    }
    if (we.d.k0()) {
        StringBuffer stringBuffer = new StringBuffer();
        stringBuffer.append("Vip章节 内容读取 chapterId:");
        stringBuffer.append(chapterItem.ChapterId);
        stringBuffer.append(" chapterName:");
        stringBuffer.append(chapterItem.ChapterName);
        stringBuffer.append(" 读取, 耗时:");
        stringBuffer.append(System.currentTimeMillis() - j11);
        stringBuffer.append("毫秒");
        Logger.d("QDReader", stringBuffer.toString());
    }
    return chapterContentItem;
}
```

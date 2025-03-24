from device_manager.utils.util_functions import (
    create_password,
    grep,
)


def test_create_password():
    password = create_password()
    assert len(password) == 8  # noqa
    assert password.isalnum()


def test_create_password_size():
    password = create_password(16)
    assert len(password) == 16  # noqa
    assert password.isalnum()


def test_grep():
    text = """\
    This is a test
    to check if the function
    can find the pattern
    in the text.
    """
    pattern = r'pattern'

    result = grep(text, pattern)
    assert result == ['    can find the pattern']


def test_grep_ignore_case():
    text = """\
    This is a test
    to check if the function
    can find the pattern
    in the text.
    """
    pattern = r'PATTERN'

    result = grep(text, pattern, ignore_case=True)
    assert result == ['    can find the pattern']


def test_grep_with_multiple_results():
    text = """\
    This is a test
    to check if the function
    can find the pattern
    in the text.
    This is a second test
    to check if the function
    finds another pattern
    in the text.
    """
    pattern = r'pattern'

    result = grep(text, pattern)
    assert result == [
        '    can find the pattern',
        '    finds another pattern',
    ]


def test_grep_with_partial_match():
    text = """CompletedProcess(args=['adb', '-s', '127.0.0.42:5555', 'shell', 'dumpsys', 'deviceidle'], returncode=0, stdout='2025-03-20T08:24:28.775085 - add:[com.android.thememanager] cu=1000 cp=7643\n  Settings:\n    flex_time_short=+1m0s0ms\n    light_after_inactive_to=+1m0s0ms\n    light_pre_idle_to=+3m0s0ms\n    light_idle_to=+5m0s0ms\n    light_idle_to_initial_flex=+1m0s0ms\n    light_max_idle_to_flex=+15m0s0ms\n    light_idle_factor=2.0\n    light_max_idle_to=+15m0s0ms\n    light_idle_maintenance_min_budget=+1m0s0ms\n    light_idle_maintenance_max_budget=+5m0s0ms\n    min_light_maintenance_time=+5s0ms\n    min_deep_maintenance_time=+30s0ms\n    inactive_to=+30m0s0ms\n    sensing_to=+4m0s0ms\n    locating_to=+30s0ms\n    location_accuracy=20.0m\n    motion_inactive_to=+10m0s0ms\n    motion_inactive_to_flex=+1m0s0ms\n    idle_after_inactive_to=+30m0s0ms\n    idle_pending_to=+5m0s0ms\n    max_idle_pending_to=+10m0s0ms\n    idle_pending_factor=2.0\n    quick_doze_delay_to=+1m0s0ms\n    idle_to=+1h0m0s0ms\n    max_idle_to=+6h0m0s0ms\n    idle_factor=2.0\n    min_time_to_alarm=+30m0s0ms\n    max_temp_app_allowlist_duration_ms=+5m0s0ms\n    mms_temp_app_allowlist_duration_ms=+1m0s0ms\n    sms_temp_app_allowlist_duration_ms=+20s0ms\n    notification_allowlist_duration_ms=+30s0ms\n    wait_for_unlock=true\n    pre_idle_factor_long=1.67\n    pre_idle_factor_short=0.33\n    use_window_alarms=true\n  Idling history:\n         normal: -2h39m35s558ms (unlocked)\n     light-idle: -1h51m46s155ms\n         normal: -1h50m8s969ms (unlocked)\n     light-idle: -1h14m37s56ms\n    light-maint: -1h8m36s56ms\n     light-idle: -1h8m30s976ms\n         normal: -1h2m50s839ms (unlocked)\n     light-idle: -49m55s564ms\n         normal: -46m36s341ms (unlocked)\n     light-idle: -35m21s71ms\n    light-maint: -29m20s56ms\n     light-idle: -29m13s412ms\n    light-maint: -17m12s62ms\n     light-idle: -17m6s965ms\n         normal: -5m32s577ms (unlocked)\n  Whitelist (except idle) system apps:\n    com.google.android.youtube\n    com.aura.oobe.deutsche\n    com.android.providers.calendar\n    com.android.updater\n    com.android.providers.downloads\n    com.google.android.apps.messaging\n    com.qualcomm.qti.telephonyservice\n    com.android.vending\n    com.qualcomm.qcrilmsgtunnel\n    com.facebook.services\n    de.telekom.tsc\n    com.qti.xdivert\n    com.android.cellbroadcastreceiver\n    com.google.android.gms\n    com.google.android.ims\n    com.android.proxyhandler\n    com.qualcomm.location\n    com.google.android.apps.turbo\n    com.android.shell\n    com.android.emergency\n    com.android.deskclock\n    com.facebook.appmanager\n    com.google.android.cellbroadcastreceiver\n    com.qualcomm.atfwd\n    com.android.providers.contacts\n    com.miui.core\n  Whitelist system apps:\n    com.google.android.youtube\n    com.aura.oobe.deutsche\n    com.android.providers.calendar\n    com.android.updater\n    com.android.providers.downloads\n    com.google.android.apps.messaging\n    com.qualcomm.qti.telephonyservice\n    com.qualcomm.qcrilmsgtunnel\n    com.facebook.services\n    de.telekom.tsc\n    com.qti.xdivert\n    com.android.cellbroadcastreceiver\n    com.google.android.gms\n    com.google.android.ims\n    com.qualcomm.location\n    com.android.shell\n    com.android.emergency\n    com.android.deskclock\n    com.google.android.cellbroadcastreceiver\n    com.qualcomm.atfwd\n    com.miui.core\n  Whitelist user apps:\n    com.milink.service\n    com.xiaomi.account\n    com.miui.msa.global\n    com.miui.securitycenter\n    com.android.providers.downloads.ui\n    com.android.stk\n    com.miui.player\n    com.miui.miservice\n    com.xiaomi.xmsf\n    com.google.android.tts\n    com.xiaomi.mipicks\n    com.miui.notes\n    com.miui.analytics\n    com.miui.weather2\n    com.android.deskclock\n    com.xiaomi.discover\n    com.android.thememanager\n    com.lbe.security.miui\n    com.miui.home\n  Whitelist (except idle) all app ids:\n    1000\n    1001\n    2000\n    6101\n    6102\n    10061\n    10063\n    10064\n    10065\n    10067\n    10072\n    10078\n    10087\n    10089\n    10093\n    10094\n    10095\n    10099\n    10118\n    10124\n    10125\n    10127\n    10131\n    10141\n    10142\n    10145\n    10146\n    10156\n    10165\n    10166\n    10167\n    10168\n    10185\n    10196\n    10197\n    10202\n    10207\n    10211\n    10217\n    10226\n    10234\n  Whitelist user app ids:\n    1000\n    1001\n    6101\n    10063\n    10067\n    10072\n    10078\n    10087\n    10099\n    10118\n    10124\n    10125\n    10127\n    10131\n    10141\n    10142\n    10185\n    10226\n    10234\n  Whitelist all app ids:\n    1000\n    1001\n    2000\n    6101\n    6102\n    10063\n    10064\n    10065\n    10067\n    10072\n    10078\n    10087\n    10093\n    10094\n    10095\n    10099\n    10118\n    10124\n    10125\n    10127\n    10131\n    10141\n    10142\n    10146\n    10156\n    10165\n    10167\n    10185\n    10196\n    10197\n    10202\n    10207\n    10211\n    10217\n    10226\n    10234\n  mLightEnabled=true  mDeepEnabled=true\n  mForceIdle=false\n  mUseMotionSensor=true mMotionSensor={Sensor name="sns_smd  Wakeup", vendor="QTI", version=1, type=17, maxRange=1.0, resolution=1.0, power=0.025, minDelay=-1}\n  mScreenOn=true\n  mScreenLocked=false\n  mNetworkConnected=true\n  mCharging=false\n  mMotionActive=false\n  mNotMoving=false\n  mMotionListener.activatedTimeElapsed=9290092\n  mLastMotionEventElapsed=0\n  0 stationary listeners registered\n  mLocating=false mHasGps=false mHasNetwork=false mLocated=false\n  mState=ACTIVE mLightState=ACTIVE\n  mInactiveTimeout=+30m0s0ms\n', stderr='')"""  # noqa
    pattern = r'mScreenOn'

    result = grep(text, pattern)
    assert result == ['  mScreenOn=true']

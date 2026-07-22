const manifest = {"name":"zapret-deck"};
const API_VERSION = 2;
const internalAPIConnection = window.__DECKY_SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED_deckyLoaderAPIInit;
if (!internalAPIConnection) {
    throw new Error('[@decky/api]: Failed to connect to the loader as as the loader API was not initialized. This is likely a bug in Decky Loader.');
}
let api;
try {
    api = internalAPIConnection.connect(API_VERSION, manifest.name);
}
catch {
    api = internalAPIConnection.connect(1, manifest.name);
    console.warn(`[@decky/api] Requested API version ${API_VERSION} but the running loader only supports version 1. Some features may not work.`);
}
if (api._version != API_VERSION) {
    console.warn(`[@decky/api] Requested API version ${API_VERSION} but the running loader only supports version ${api._version}. Some features may not work.`);
}
const callable = api.callable;
const toaster = api.toaster;
const definePlugin = (fn) => {
    return (...args) => {
        return fn(...args);
    };
};

var DefaultContext = {
  color: undefined,
  size: undefined,
  className: undefined,
  style: undefined,
  attr: undefined
};
var IconContext = SP_REACT.createContext && /*#__PURE__*/SP_REACT.createContext(DefaultContext);

var _excluded = ["attr", "size", "title"];
function _objectWithoutProperties(e, t) { if (null == e) return {}; var o, r, i = _objectWithoutPropertiesLoose(e, t); if (Object.getOwnPropertySymbols) { var n = Object.getOwnPropertySymbols(e); for (r = 0; r < n.length; r++) o = n[r], -1 === t.indexOf(o) && {}.propertyIsEnumerable.call(e, o) && (i[o] = e[o]); } return i; }
function _objectWithoutPropertiesLoose(r, e) { if (null == r) return {}; var t = {}; for (var n in r) if ({}.hasOwnProperty.call(r, n)) { if (-1 !== e.indexOf(n)) continue; t[n] = r[n]; } return t; }
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
function ownKeys(e, r) { var t = Object.keys(e); if (Object.getOwnPropertySymbols) { var o = Object.getOwnPropertySymbols(e); r && (o = o.filter(function (r) { return Object.getOwnPropertyDescriptor(e, r).enumerable; })), t.push.apply(t, o); } return t; }
function _objectSpread(e) { for (var r = 1; r < arguments.length; r++) { var t = null != arguments[r] ? arguments[r] : {}; r % 2 ? ownKeys(Object(t), true).forEach(function (r) { _defineProperty(e, r, t[r]); }) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(t)) : ownKeys(Object(t)).forEach(function (r) { Object.defineProperty(e, r, Object.getOwnPropertyDescriptor(t, r)); }); } return e; }
function _defineProperty(e, r, t) { return (r = _toPropertyKey(r)) in e ? Object.defineProperty(e, r, { value: t, enumerable: true, configurable: true, writable: true }) : e[r] = t, e; }
function _toPropertyKey(t) { var i = _toPrimitive(t, "string"); return "symbol" == typeof i ? i : i + ""; }
function _toPrimitive(t, r) { if ("object" != typeof t || !t) return t; var e = t[Symbol.toPrimitive]; if (void 0 !== e) { var i = e.call(t, r); if ("object" != typeof i) return i; throw new TypeError("@@toPrimitive must return a primitive value."); } return ("string" === r ? String : Number)(t); }
function Tree2Element(tree) {
  return tree && tree.map((node, i) => /*#__PURE__*/SP_REACT.createElement(node.tag, _objectSpread({
    key: i
  }, node.attr), Tree2Element(node.child)));
}
function GenIcon(data) {
  return props => /*#__PURE__*/SP_REACT.createElement(IconBase, _extends({
    attr: _objectSpread({}, data.attr)
  }, props), Tree2Element(data.child));
}
function IconBase(props) {
  var elem = conf => {
    var attr = props.attr,
      size = props.size,
      title = props.title,
      svgProps = _objectWithoutProperties(props, _excluded);
    var computedSize = size || conf.size || "1em";
    var className;
    if (conf.className) className = conf.className;
    if (props.className) className = (className ? className + " " : "") + props.className;
    return /*#__PURE__*/SP_REACT.createElement("svg", _extends({
      stroke: "currentColor",
      fill: "currentColor",
      strokeWidth: "0"
    }, conf.attr, attr, svgProps, {
      className: className,
      style: _objectSpread(_objectSpread({
        color: props.color || conf.color
      }, conf.style), props.style),
      height: computedSize,
      width: computedSize,
      xmlns: "http://www.w3.org/2000/svg"
    }), title && /*#__PURE__*/SP_REACT.createElement("title", null, title), props.children);
  };
  return IconContext !== undefined ? /*#__PURE__*/SP_REACT.createElement(IconContext.Consumer, null, conf => elem(conf)) : elem(DefaultContext);
}

// THIS FILE IS AUTO GENERATED
function FaShieldAlt (props) {
  return GenIcon({"attr":{"viewBox":"0 0 512 512"},"child":[{"tag":"path","attr":{"d":"M466.5 83.7l-192-80a48.15 48.15 0 0 0-36.9 0l-192 80C27.7 91.1 16 108.6 16 128c0 198.5 114.5 335.7 221.5 380.3 11.8 4.9 25.1 4.9 36.9 0C360.1 472.6 496 349.3 496 128c0-19.4-11.7-36.9-29.5-44.3zM256.1 446.3l-.1-381 175.9 73.3c-3.3 151.4-82.1 261.1-175.8 307.7z"},"child":[]}]})(props);
}

const getStatus = callable("get_status");
const setServiceState = callable("set_service_state");
const getStrategies = callable("get_strategies");
const applyStrategy = callable("apply_strategy");
const generateWarp = callable("generate_warp");
const startAutotune = callable("start_autotune");
const getSteamLanguage = callable("get_steam_language");
const updateResources = callable("update_resources");
const translations = {
    english: {
        pluginTitle: "Zapret Deck",
        zapretTitle: "Zapret Bypass",
        warpTitle: "WARP",
        statusTitle: "Status",
        statusActive: "Active",
        statusInactive: "Inactive",
        zapretSettings: "Zapret Settings",
        warpSettings: "WARP Settings",
        strategySelect: "Bypass Strategies",
        runAutotune: "Auto-detect Strategy",
        autotuneRunning: "Detecting... (please wait)",
        editHostlist: "Edit Blocked Hostlist",
        hostlistTitle: "Blocked Domain List",
        hostlistPlaceholder: "Enter one domain per line (e.g. youtube.com)",
        save: "Save",
        cancel: "Cancel",
        warpStatus: "Status",
        warpRegistered: "Registered",
        warpNotRegistered: "Not Registered",
        generateWarp: "Generate WARP Account",
        generatingWarp: "Generating...",
        success: "Success",
        error: "Error",
        noWorkingStrategy: "No working strategy found",
        autotuneComplete: "Auto-detection complete!",
        appliedStrategy: "Applied strategy",
        updateResources: "Update Lists & Strategies",
        updating: "Updating...",
        language: "Language",
    },
    russian: {
        pluginTitle: "Zapret Deck",
        zapretTitle: "Обход Zapret",
        warpTitle: "WARP",
        statusTitle: "Состояние",
        statusActive: "Активен",
        statusInactive: "Неактивен",
        zapretSettings: "Настройки Zapret",
        warpSettings: "Настройки WARP",
        strategySelect: "Стратегии обхода",
        runAutotune: "Автоподбор стратегии",
        autotuneRunning: "Подбор стратегии... (ждите)",
        editHostlist: "Редактировать список сайтов",
        hostlistTitle: "Список заблокированных доменов",
        hostlistPlaceholder: "Введите по одному домену на строку (например, youtube.com)",
        save: "Сохранить",
        cancel: "Отмена",
        warpStatus: "Статус",
        warpRegistered: "Зарегистрирован",
        warpNotRegistered: "Не зарегистрирован",
        generateWarp: "Сгенерировать WARP аккаунт",
        generatingWarp: "Генерация...",
        success: "Успех",
        error: "Ошибка",
        noWorkingStrategy: "Рабочая стратегия не найдена",
        autotuneComplete: "Автоподбор завершен!",
        appliedStrategy: "Применена стратегия",
        updateResources: "Обновить списки и стратегии",
        updating: "Обновление...",
        language: "Язык",
    },
    ukrainian: {
        pluginTitle: "Zapret Deck",
        zapretTitle: "Обхід Zapret",
        warpTitle: "WARP",
        statusTitle: "Стан",
        statusActive: "Активний",
        statusInactive: "Неактивний",
        zapretSettings: "Налаштування Zapret",
        warpSettings: "Налаштування WARP",
        strategySelect: "Стратегії обходу",
        runAutotune: "Автопідбір стратегії",
        autotuneRunning: "Підбір... (зачекайте)",
        editHostlist: "Редагувати список сайтів",
        hostlistTitle: "Список заблокованих доменів",
        hostlistPlaceholder: "Введіть один домен на рядок (наприклад, youtube.com)",
        save: "Зберегти",
        cancel: "Скасувати",
        warpStatus: "Статус",
        warpRegistered: "Зареєстрований",
        warpNotRegistered: "Не зареєстрований",
        generateWarp: "Згенерувати акаунт WARP",
        generatingWarp: "Генерація...",
        success: "Успіх",
        error: "Помилка",
        noWorkingStrategy: "Робочу стратегію не знайдено",
        autotuneComplete: "Автопідбір завершено!",
        appliedStrategy: "Застосовано стратегію",
        updateResources: "Оновити списки та стратегії",
        updating: "Оновлення...",
        language: "Мова",
    },
    turkish: {
        pluginTitle: "Zapret Deck",
        zapretTitle: "Zapret Atlatma",
        warpTitle: "WARP",
        statusTitle: "Durum",
        statusActive: "Aktif",
        statusInactive: "Pasif",
        zapretSettings: "Zapret Ayarları",
        warpSettings: "WARP Ayarları",
        strategySelect: "Atlatma Stratejileri",
        runAutotune: "Stratejiyi Otomatik Algıla",
        autotuneRunning: "Algılanıyor... (lütfen bekleyin)",
        editHostlist: "Engelli Siteleri Düzenle",
        hostlistTitle: "Engelli Alan Adı Listesi",
        hostlistPlaceholder: "Satır başına bir alan adı girin (örn. youtube.com)",
        save: "Kaydet",
        cancel: "İptal",
        warpStatus: "Durum",
        warpRegistered: "Kayıtlı",
        warpNotRegistered: "Kayıtlı Değil",
        generateWarp: "WARP Hesabı Oluştur",
        generatingWarp: "Oluşturuluyor...",
        success: "Başarılı",
        error: "Hata",
        noWorkingStrategy: "Çalışan strateji bulunamadı",
        autotuneComplete: "Otomatik algılama tamamlandı!",
        appliedStrategy: "Uygulanan strateji",
        updateResources: "Listeleri ve Stratejileri Güncelle",
        updating: "Güncelleniyor...",
        language: "Dil",
    },
    arabic: {
        pluginTitle: "Zapret Deck",
        zapretTitle: "تخطي Zapret",
        warpTitle: "WARP",
        statusTitle: "الحالة",
        statusActive: "نشط",
        statusInactive: "غير نشط",
        zapretSettings: "إعدادات Zapret",
        warpSettings: "إعدادات WARP",
        strategySelect: "استراتيجيات التخطي",
        runAutotune: "الكشف التلقائي عن الاستراتيجية",
        autotuneRunning: "جاري الكشف... (يرجى الانتظار)",
        editHostlist: "تعديل قائمة المواقع المحجوبة",
        hostlistTitle: "قائمة النطاقات المحجوبة",
        hostlistPlaceholder: "أدخل نطاقًا واحدًا في كل سطر (مثال: youtube.com)",
        save: "حفظ",
        cancel: "إلغاء",
        warpStatus: "الحالة",
        warpRegistered: "مسجل",
        warpNotRegistered: "غير مسجل",
        generateWarp: "إنشاء حساب WARP",
        generatingWarp: "جاري الإنشاء...",
        success: "نجاح",
        error: "خطأ",
        noWorkingStrategy: "لم يتم العثور على استراتيجية صالحة",
        autotuneComplete: "اكتمل الكشف التلقائي!",
        appliedStrategy: "تم تطبيق الاستراتيجية",
        updateResources: "تحديث القوائم والاستراتيجيات",
        updating: "جاري التحديث...",
        language: "اللغة",
    },
    farsi: {
        pluginTitle: "Zapret Deck",
        zapretTitle: "دور زدن Zapret",
        warpTitle: "WARP",
        statusTitle: "وضعیت",
        statusActive: "فعال",
        statusInactive: "غیرفعال",
        zapretSettings: "تنظیمات Zapret",
        warpSettings: "تنظیمات WARP",
        strategySelect: "استراتژی‌های دور زدن",
        runAutotune: "تشخیص خودکار استراتژی",
        autotuneRunning: "در حال تشخیص... (لطفاً صبر کنید)",
        editHostlist: "ویرایش لیست دامنه‌های مسدود شده",
        hostlistTitle: "لیست دامنه‌های مسدود شده",
        hostlistPlaceholder: "در هر سطر یک دامنه وارد کنید (مثال: youtube.com)",
        save: "ذخیره",
        cancel: "لغو",
        warpStatus: "وضعیت",
        warpRegistered: "ثبت شده",
        warpNotRegistered: "ثبت نشده",
        generateWarp: "ساخت اکانت WARP",
        generatingWarp: "در حال ساخت...",
        success: "موفقیت",
        error: "خطا",
        noWorkingStrategy: "استراتژی کارآمدی یافت نشد",
        autotuneComplete: "تشخیص خودکار به پایان رسید!",
        appliedStrategy: "استراتژی اعمال شد",
        updateResources: "بروزرسانی لیست‌ها و استراتژی‌ها",
        updating: "در حال بروزرسانی...",
        language: "زبان",
    },
    persian: {
        pluginTitle: "Zapret Deck",
        zapretTitle: "دور زدن Zapret",
        warpTitle: "WARP",
        statusTitle: "وضعیت",
        statusActive: "فعال",
        statusInactive: "غیرفعال",
        zapretSettings: "تنظیمات Zapret",
        warpSettings: "تنظیمات WARP",
        strategySelect: "استراتژی‌های دور زدن",
        runAutotune: "تشخیص خودکار استراتژی",
        autotuneRunning: "در حال تشخیص... (لطفاً صبر کنید)",
        editHostlist: "ویرایش لیست دامنه‌های مسدود شده",
        hostlistTitle: "لیست دامنه‌های مسدود شده",
        hostlistPlaceholder: "در هر سطر یک دامنه وارد کنید (مثال: youtube.com)",
        save: "ذخیره",
        cancel: "لغو",
        warpStatus: "وضعیت ثبت‌نام",
        warpRegistered: "ثبت شده",
        warpNotRegistered: "ثبت نشده",
        generateWarp: "ساخت اکانت WARP",
        generatingWarp: "در حال ساخت...",
        success: "موفقیت",
        error: "خطا",
        noWorkingStrategy: "استراتژی کارآمدی یافت نشد",
        autotuneComplete: "تشخیص خودکار به پایان رسید!",
        appliedStrategy: "استراتژی اعمال شد",
        updateResources: "بروزرسانی لیست‌ها و استراتژی‌ها",
        updating: "در حال بروزرسانی...",
        language: "زبان",
    },
    schinese: {
        pluginTitle: "Zapret Deck",
        zapretTitle: "Zapret 绕过",
        warpTitle: "WARP",
        statusTitle: "状态",
        statusActive: "已启用",
        statusInactive: "已禁用",
        zapretSettings: "Zapret 设置",
        warpSettings: "WARP 设置",
        strategySelect: "绕过策略",
        runAutotune: "自动检测策略",
        autotuneRunning: "检测中... (请稍候)",
        editHostlist: "编辑分流域名列表",
        hostlistTitle: "被屏蔽的域名列表",
        hostlistPlaceholder: "每行输入一个域名（例如 youtube.com）",
        save: "保存",
        cancel: "取消",
        warpStatus: "状态",
        warpRegistered: "已注册",
        warpNotRegistered: "未注册",
        generateWarp: "生成 WARP 账号",
        generatingWarp: "生成中...",
        success: "成功",
        error: "错误",
        noWorkingStrategy: "未找到可用策略",
        autotuneComplete: "自动检测完成！",
        appliedStrategy: "已应用策略",
        updateResources: "更新域名列表与策略",
        updating: "更新中...",
        language: "语言",
    },
    tchinese: {
        pluginTitle: "Zapret Deck",
        zapretTitle: "Zapret 繞過",
        warpTitle: "WARP",
        statusTitle: "狀態",
        statusActive: "已啟用",
        statusInactive: "已停用",
        zapretSettings: "Zapret 設定",
        warpSettings: "WARP 設定",
        strategySelect: "繞過策略",
        runAutotune: "自動檢測策略",
        autotuneRunning: "檢測中... (請稍候)",
        editHostlist: "編輯分流網域名稱列表",
        hostlistTitle: "被封鎖的網域名稱列表",
        hostlistPlaceholder: "每行輸入一個網網域名稱（例如 youtube.com）",
        save: "儲存",
        cancel: "取消",
        warpStatus: "狀態",
        warpRegistered: "已註冊",
        warpNotRegistered: "未註冊",
        generateWarp: "生成 WARP 帳號",
        generatingWarp: "生成中...",
        success: "成功",
        error: "錯誤",
        noWorkingStrategy: "未找到可用策略",
        autotuneComplete: "自動檢測完成！",
        appliedStrategy: "已應用策略",
        updateResources: "更新網網域名稱列表與策略",
        updating: "更新中...",
        language: "語言",
    }
};
const LANGUAGE_OPTIONS = [
    { label: "English", data: "english" },
    { label: "Русский", data: "russian" },
    { label: "Українська", data: "ukrainian" },
    { label: "Türkçe", data: "turkish" },
    { label: "العربية", data: "arabic" },
    { label: "فارسی", data: "persian" },
    { label: "简体中文", data: "schinese" },
    { label: "繁體中文", data: "tchinese" },
];
// Редактор списка сайтов убран
const Content = () => {
    const [status, setStatus] = SP_REACT.useState(null);
    const [strategies, setStrategies] = SP_REACT.useState([]);
    const [lang, setLang] = SP_REACT.useState("english");
    const [loadingWarp, setLoadingWarp] = SP_REACT.useState(false);
    const [updatingResources, setUpdatingResources] = SP_REACT.useState(false);
    const [strategiesExpanded, setStrategiesExpanded] = SP_REACT.useState(false);
    const t = SP_REACT.useMemo(() => {
        return translations[lang] || translations.english;
    }, [lang]);
    const refreshStatus = SP_REACT.useCallback(async () => {
        try {
            const res = await getStatus();
            setStatus(res);
            const strats = await getStrategies();
            setStrategies(strats || []);
        }
        catch (e) {
            console.error("Failed to get status", e);
        }
    }, []);
    const prevInProgress = SP_REACT.useRef(false);
    SP_REACT.useEffect(() => {
        if (status) {
            if (prevInProgress.current && !status.autotune_in_progress) {
                // Автоподбор только что завершился!
                if (status.zapret_enabled || status.current_strategy) {
                    const stratName = status.current_strategy_name || "Авто";
                    toaster.toast({
                        title: t.pluginTitle,
                        body: `${t.autotuneComplete} ${t.appliedStrategy}: ${stratName}`,
                    });
                }
                else {
                    toaster.toast({
                        title: t.error,
                        body: t.noWorkingStrategy || "Не найдено подходящих стратегий",
                    });
                }
            }
            prevInProgress.current = status.autotune_in_progress;
        }
    }, [status, t]);
    SP_REACT.useEffect(() => {
        refreshStatus();
        const interval = setInterval(refreshStatus, 3000);
        getSteamLanguage().then((l) => setLang(l || "english")).catch(() => setLang("english"));
        return () => clearInterval(interval);
    }, [refreshStatus]);
    const handleServiceToggle = async (service, enabled) => {
        try {
            const res = await setServiceState(service, enabled);
            if (res.success) {
                toaster.toast({
                    title: t.pluginTitle,
                    body: `${service === "zapret" ? t.zapretTitle : t.warpTitle}: ${enabled ? t.statusActive : t.statusInactive}`,
                });
            }
            else {
                toaster.toast({
                    title: t.error,
                    body: res.error || "Failed to toggle service",
                });
            }
            refreshStatus();
        }
        catch (e) {
            console.error(e);
        }
    };
    const handleStrategyChange = async (args, isSelected) => {
        try {
            const targetArgs = isSelected ? "" : args;
            const res = await applyStrategy(targetArgs);
            if (res.success) {
                toaster.toast({
                    title: t.success,
                    body: isSelected ? "Выбор стратегии отменен" : t.appliedStrategy,
                });
            }
            refreshStatus();
        }
        catch (e) {
            console.error(e);
        }
    };
    const handleGenerateWarp = async () => {
        setLoadingWarp(true);
        try {
            const res = await generateWarp();
            if (res.success) {
                toaster.toast({
                    title: t.success,
                    body: "WARP Account generated successfully!",
                });
            }
            else {
                toaster.toast({
                    title: t.error,
                    body: "Failed to generate WARP account",
                });
            }
            refreshStatus();
        }
        catch (e) {
            console.error(e);
        }
        finally {
            setLoadingWarp(false);
        }
    };
    const handleUpdateResources = async () => {
        setUpdatingResources(true);
        try {
            const res = await updateResources();
            if (res.success) {
                toaster.toast({
                    title: t.pluginTitle,
                    body: `${t.updateResources}: ${t.success}`,
                });
            }
            else {
                toaster.toast({
                    title: t.error,
                    body: "Failed to update resources",
                });
            }
        }
        catch (e) {
            console.error(e);
        }
        finally {
            setUpdatingResources(false);
        }
    };
    const handleStartAutotune = async () => {
        try {
            const res = await startAutotune();
            if (res.success) {
                toaster.toast({
                    title: t.pluginTitle,
                    body: t.autotuneRunning,
                });
                // Частый опрос состояния каждые 500мс во время подбора
                const pollInterval = setInterval(async () => {
                    try {
                        const st = await getStatus();
                        setStatus(st);
                        const strats = await getStrategies();
                        setStrategies(strats || []);
                        if (!st.autotune_in_progress) {
                            clearInterval(pollInterval);
                            // Дополнительное подтверждение статуса через 500мс и 1.5с
                            setTimeout(refreshStatus, 500);
                            setTimeout(refreshStatus, 1500);
                        }
                    }
                    catch (err) {
                        console.error(err);
                    }
                }, 500);
            }
            else {
                toaster.toast({
                    title: t.error,
                    body: res.error || "Failed to start autotune",
                });
            }
        }
        catch (e) {
            console.error(e);
        }
    };
    if (!status) {
        return SP_JSX.jsx(DFL.PanelSection, { children: SP_JSX.jsx(DFL.PanelSectionRow, { children: "Loading..." }) });
    }
    const isZapretActive = Boolean(!status.autotune_in_progress && (status.zapret_enabled || status.zapret_active));
    const isWarpActive = Boolean(status.warp_enabled || status.warp_active);
    return (SP_JSX.jsxs(DFL.PanelSection, { children: [SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: () => handleServiceToggle("zapret", !isZapretActive), children: SP_JSX.jsxs("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "center", width: "100%" }, children: [SP_JSX.jsx("span", { style: { fontWeight: "normal", color: "inherit" }, children: t.zapretTitle }), SP_JSX.jsx("span", { style: { fontSize: "12px", color: isZapretActive ? "#1a9fff" : "#888", fontWeight: "bold" }, children: isZapretActive ? t.statusActive : t.statusInactive })] }) }) }), SP_JSX.jsx("div", { style: { display: "flex", justifyContent: "center", width: "100%", padding: "12px 0 6px 0" }, children: SP_JSX.jsx("span", { style: { fontSize: "11px", fontWeight: "bold", color: "#a5a5a5", textTransform: "uppercase", letterSpacing: "0.5px" }, children: t.zapretSettings }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: () => setStrategiesExpanded(!strategiesExpanded), children: SP_JSX.jsxs("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "center", width: "100%" }, children: [SP_JSX.jsx("span", { style: { fontWeight: "bold", color: "#a5a5a5", fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.5px" }, children: t.strategySelect }), SP_JSX.jsx("span", { style: { fontSize: "10px", color: "#888" }, children: strategiesExpanded ? "▼" : "▶" })] }) }) }), strategiesExpanded && (SP_JSX.jsx("div", { style: { maxHeight: "200px", overflowY: "auto", paddingRight: "4px", marginBottom: "8px", border: "1px solid #333", borderRadius: "4px", padding: "4px" }, children: strategies.map((s, idx) => {
                    const isSelected = status.current_strategy_name === s.name.replace(" (Auto)", "");
                    return (SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsxs("div", { style: { position: "relative", width: "100%" }, children: [SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: () => handleStrategyChange(s.args, isSelected), children: SP_JSX.jsx("div", { style: { display: "flex", alignItems: "center", width: "100%" }, children: SP_JSX.jsx("span", { style: { fontWeight: isSelected ? "bold" : "normal", color: isSelected ? "#1a9fff" : "inherit" }, children: s.name }) }) }), isSelected && (SP_JSX.jsx("div", { style: {
                                        position: "absolute",
                                        top: 0,
                                        left: 0,
                                        right: 0,
                                        bottom: 0,
                                        border: "1.5px solid #1a9fff",
                                        borderRadius: "4px",
                                        pointerEvents: "none",
                                        backgroundColor: "rgba(26, 159, 255, 0.1)"
                                    } }))] }) }, idx));
                }) })), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: handleStartAutotune, disabled: status.autotune_in_progress, children: status.autotune_in_progress ? t.autotuneRunning : t.runAutotune }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: handleUpdateResources, disabled: updatingResources, children: updatingResources ? t.updating : t.updateResources }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: () => handleServiceToggle("warp", !isWarpActive), children: SP_JSX.jsxs("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "center", width: "100%" }, children: [SP_JSX.jsx("span", { style: { fontWeight: "normal", color: "inherit" }, children: t.warpTitle }), SP_JSX.jsx("span", { style: { fontSize: "12px", color: isWarpActive ? "#1a9fff" : "#888", fontWeight: "bold" }, children: isWarpActive ? t.statusActive : t.statusInactive })] }) }) }), SP_JSX.jsx("div", { style: { display: "flex", justifyContent: "center", width: "100%", padding: "12px 0 6px 0" }, children: SP_JSX.jsx("span", { style: { fontSize: "11px", fontWeight: "bold", color: "#a5a5a5", textTransform: "uppercase", letterSpacing: "0.5px" }, children: t.warpSettings }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", children: SP_JSX.jsxs("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "center", width: "100%" }, children: [SP_JSX.jsx("span", { children: t.warpStatus }), SP_JSX.jsx("span", { style: { color: status.warp_registered ? "#4caf50" : "#ff9800", fontWeight: "bold", fontSize: "12px" }, children: status.warp_registered ? t.warpRegistered : t.warpNotRegistered })] }) }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: handleGenerateWarp, disabled: loadingWarp, children: loadingWarp ? t.generatingWarp : t.generateWarp }) }), SP_JSX.jsx("div", { style: { display: "flex", justifyContent: "center", width: "100%", padding: "12px 0 6px 0" }, children: SP_JSX.jsx("span", { style: { fontSize: "11px", fontWeight: "bold", color: "#a5a5a5", textTransform: "uppercase", letterSpacing: "0.5px" }, children: t.language }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.Field, { label: t.language, children: SP_JSX.jsx(DFL.Dropdown, { selectedOption: lang, onChange: (opt) => setLang(opt.data), rgOptions: LANGUAGE_OPTIONS }) }) })] }));
};
var index = definePlugin(() => {
    return {
        name: "Zapret Deck",
        titleView: SP_JSX.jsx("div", { className: DFL.staticClasses.Title, children: "Zapret Deck" }),
        content: SP_JSX.jsx(Content, {}),
        icon: SP_JSX.jsx(FaShieldAlt, {}),
        onDismount() {
            // Очистка
        },
    };
});

export { index as default };
//# sourceMappingURL=index.js.map

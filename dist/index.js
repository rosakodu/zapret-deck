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
const setMode = callable("set_mode");
const getStrategies = callable("get_strategies");
const applyStrategy = callable("apply_strategy");
const generateWarp = callable("generate_warp");
const getHostlist = callable("get_hostlist");
const saveHostlist = callable("save_hostlist");
const startAutotune = callable("start_autotune");
const getSteamLanguage = callable("get_steam_language");
const translations = {
    english: {
        pluginTitle: "Zapret & WARP Bypass",
        modeTitle: "Operation Mode",
        modeOff: "Disabled",
        modeZapret: "Zapret (DPI Bypass)",
        modeWarp: "WARP (MASQUE VPN)",
        statusTitle: "Service Status",
        statusActive: "Active",
        statusInactive: "Inactive",
        zapretSettings: "Zapret Settings",
        warpSettings: "WARP Settings",
        strategySelect: "Bypass Strategy",
        runAutotune: "Auto-detect Strategy",
        autotuneRunning: "Detecting... (please wait)",
        editHostlist: "Edit Blocked Hostlist",
        hostlistTitle: "Blocked Domain List",
        hostlistPlaceholder: "Enter one domain per line (e.g. youtube.com)",
        save: "Save",
        cancel: "Cancel",
        warpStatus: "Registration Status",
        warpRegistered: "Registered",
        warpNotRegistered: "Not Registered",
        generateWarp: "Generate WARP Account",
        generatingWarp: "Generating...",
        success: "Success",
        error: "Error",
        noWorkingStrategy: "No working strategy found",
        autotuneComplete: "Auto-detection complete!",
        appliedStrategy: "Applied strategy",
    },
    russian: {
        pluginTitle: "Обход Блокировок Zapret & WARP",
        modeTitle: "Режим работы",
        modeOff: "Выключен",
        modeZapret: "Zapret (Обход DPI)",
        modeWarp: "WARP (MASQUE VPN)",
        statusTitle: "Состояние службы",
        statusActive: "Активна",
        statusInactive: "Неактивна",
        zapretSettings: "Настройки Zapret",
        warpSettings: "Настройки WARP",
        strategySelect: "Стратегия обхода",
        runAutotune: "Автоподбор стратегии",
        autotuneRunning: "Подбор стратегии... (ждите)",
        editHostlist: "Редактировать список сайтов",
        hostlistTitle: "Список заблокированных доменов",
        hostlistPlaceholder: "Введите по одному домену на строку (например, youtube.com)",
        save: "Сохранить",
        cancel: "Отмена",
        warpStatus: "Статус регистрации",
        warpRegistered: "Зарегистрирован",
        warpNotRegistered: "Не зарегистрирован",
        generateWarp: "Сгенерировать WARP аккаунт",
        generatingWarp: "Генерация...",
        success: "Успех",
        error: "Ошибка",
        noWorkingStrategy: "Рабочая стратегия не найдена",
        autotuneComplete: "Автоподбор завершен!",
        appliedStrategy: "Применена стратегия",
    },
    ukrainian: {
        pluginTitle: "Обхід Блокувань Zapret & WARP",
        modeTitle: "Режим роботи",
        modeOff: "Вимкнено",
        modeZapret: "Zapret (Обхід DPI)",
        modeWarp: "WARP (MASQUE VPN)",
        statusTitle: "Стан служби",
        statusActive: "Активна",
        statusInactive: "Неактивна",
        zapretSettings: "Налаштування Zapret",
        warpSettings: "Налаштування WARP",
        strategySelect: "Стратегія обходу",
        runAutotune: "Автопідбір стратегії",
        autotuneRunning: "Підбір... (зачекайте)",
        editHostlist: "Редагувати список сайтів",
        hostlistTitle: "Список заблокованих доменів",
        hostlistPlaceholder: "Введіть один домен на рядок (наприклад, youtube.com)",
        save: "Зберегти",
        cancel: "Скасувати",
        warpStatus: "Статус реєстрації",
        warpRegistered: "Зареєстрований",
        warpNotRegistered: "Не зареєстрований",
        generateWarp: "Згенерувати акаунт WARP",
        generatingWarp: "Генерація...",
        success: "Успіх",
        error: "Помилка",
        noWorkingStrategy: "Робочу стратегію не знайдено",
        autotuneComplete: "Автопідбір завершено!",
        appliedStrategy: "Застосовано стратегію",
    },
    turkish: {
        pluginTitle: "Zapret & WARP Engelleme Kaldırıcı",
        modeTitle: "Çalışma Modu",
        modeOff: "Devre Dışı",
        modeZapret: "Zapret (DPI Atlatma)",
        modeWarp: "WARP (MASQUE VPN)",
        statusTitle: "Servis Durumu",
        statusActive: "Aktif",
        statusInactive: "Pasif",
        zapretSettings: "Zapret Ayarları",
        warpSettings: "WARP Ayarları",
        strategySelect: "Atlatma Stratejisi",
        runAutotune: "Stratejiyi Otomatik Algıla",
        autotuneRunning: "Algılanıyor... (lütfen bekleyin)",
        editHostlist: "Engelli Siteleri Düzenle",
        hostlistTitle: "Engelli Alan Adı Listesi",
        hostlistPlaceholder: "Satır başına bir alan adı girin (örn. youtube.com)",
        save: "Kaydet",
        cancel: "İptal",
        warpStatus: "Kayıt Durumu",
        warpRegistered: "Kayıtlı",
        warpNotRegistered: "Kayıtlı Değil",
        generateWarp: "WARP Hesabı Oluştur",
        generatingWarp: "Oluşturuluyor...",
        success: "Başarılı",
        error: "Hata",
        noWorkingStrategy: "Çalışan strateji bulunamadı",
        autotuneComplete: "Otomatik algılama tamamlandı!",
        appliedStrategy: "Uygulanan strateji",
    }
};
const HostlistModal = ({ closeModal, onSave, currentHosts, t, }) => {
    const [hosts, setHosts] = SP_REACT.useState(currentHosts);
    return (SP_JSX.jsxs(DFL.ModalRoot, { children: [SP_JSX.jsx(DFL.DialogHeader, { children: t.hostlistTitle }), SP_JSX.jsx(DFL.DialogBody, { children: SP_JSX.jsx(DFL.TextField, { label: t.hostlistPlaceholder, value: hosts, onChange: (e) => setHosts(e.target.value) }) }), SP_JSX.jsxs(DFL.DialogFooter, { children: [SP_JSX.jsx(DFL.DialogButton, { onClick: closeModal, children: t.cancel }), SP_JSX.jsx(DFL.DialogButton, { onClick: () => {
                            onSave(hosts);
                            closeModal();
                        }, children: t.save })] })] }));
};
const Content = () => {
    const [status, setStatus] = SP_REACT.useState(null);
    const [strategies, setStrategies] = SP_REACT.useState([]);
    const [lang, setLang] = SP_REACT.useState("english");
    const [hostlist, setHostlist] = SP_REACT.useState("");
    const [loadingWarp, setLoadingWarp] = SP_REACT.useState(false);
    const t = SP_REACT.useMemo(() => {
        return translations[lang] || translations.english;
    }, [lang]);
    const refreshStatus = SP_REACT.useCallback(async () => {
        try {
            const res = await getStatus();
            setStatus(res);
        }
        catch (e) {
            console.error("Failed to get status", e);
        }
    }, []);
    SP_REACT.useEffect(() => {
        refreshStatus();
        const interval = setInterval(refreshStatus, 3000);
        getSteamLanguage().then((l) => setLang(l || "english")).catch(() => setLang("english"));
        getStrategies().then((strats) => setStrategies(strats || [])).catch(() => setStrategies([]));
        getHostlist().then((hosts) => setHostlist(hosts || "")).catch(() => setHostlist(""));
        return () => clearInterval(interval);
    }, [refreshStatus]);
    const handleModeChange = async (mode) => {
        try {
            const res = await setMode(mode);
            if (res.success) {
                toaster.toast({
                    title: t.pluginTitle,
                    body: `${t.modeTitle}: ${mode === "off" ? t.modeOff : mode === "zapret" ? t.modeZapret : t.modeWarp}`,
                });
            }
            else {
                toaster.toast({
                    title: t.error,
                    body: res.error || "Failed to switch mode",
                });
            }
            refreshStatus();
        }
        catch (e) {
            console.error(e);
        }
    };
    const handleStrategyChange = async (args) => {
        try {
            const res = await applyStrategy(args);
            if (res.success) {
                toaster.toast({
                    title: t.success,
                    body: t.appliedStrategy,
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
    const handleStartAutotune = async () => {
        try {
            const res = await startAutotune();
            if (res.success) {
                toaster.toast({
                    title: t.pluginTitle,
                    body: t.autotuneRunning,
                });
            }
            else {
                toaster.toast({
                    title: t.error,
                    body: res.error || "Failed to start autotune",
                });
            }
            refreshStatus();
        }
        catch (e) {
            console.error(e);
        }
    };
    const handleEditHostlist = () => {
        DFL.showModal(SP_JSX.jsx(HostlistModal, { closeModal: () => { }, onSave: async (hosts) => {
                setHostlist(hosts);
                const res = await saveHostlist(hosts);
                if (res.success) {
                    toaster.toast({
                        title: t.success,
                        body: t.appliedStrategy,
                    });
                }
            }, currentHosts: hostlist, t: t }));
    };
    if (!status) {
        return SP_JSX.jsx(DFL.PanelSection, { children: SP_JSX.jsx(DFL.PanelSectionRow, { children: "Loading..." }) });
    }
    const modeOptions = [
        { data: "off", label: t.modeOff },
        { data: "zapret", label: t.modeZapret },
        { data: "warp", label: t.modeWarp },
    ];
    const strategyOptions = strategies.map((s) => ({
        data: s.args,
        label: s.name,
    }));
    const isServiceActive = status.mode === "zapret" ? status.zapret_active : status.mode === "warp" ? status.warp_active : false;
    return (SP_JSX.jsxs(DFL.PanelSection, { title: t.pluginTitle, children: [SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.DropdownItem, { label: t.modeTitle, rgOptions: modeOptions, selectedOption: status.mode, onChange: (opt) => handleModeChange(opt.data) }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsxs("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "center" }, children: [SP_JSX.jsx("span", { children: t.statusTitle }), SP_JSX.jsx("span", { style: { color: isServiceActive ? "#4caf50" : "#f44336", fontWeight: "bold" }, children: isServiceActive ? t.statusActive : t.statusInactive })] }) }), status.mode === "zapret" && (SP_JSX.jsxs(DFL.PanelSection, { title: t.zapretSettings, children: [SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.DropdownItem, { label: t.strategySelect, rgOptions: strategyOptions, selectedOption: status.current_strategy, onChange: (opt) => handleStrategyChange(opt.data) }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: handleStartAutotune, disabled: status.autotune_in_progress, children: status.autotune_in_progress ? t.autotuneRunning : t.runAutotune }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: handleEditHostlist, children: t.editHostlist }) })] })), status.mode === "warp" && (SP_JSX.jsxs(DFL.PanelSection, { title: t.warpSettings, children: [SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsxs("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "center" }, children: [SP_JSX.jsx("span", { children: t.warpStatus }), SP_JSX.jsx("span", { style: { color: status.warp_registered ? "#4caf50" : "#ff9800", fontWeight: "bold" }, children: status.warp_registered ? t.warpRegistered : t.warpNotRegistered })] }) }), SP_JSX.jsx(DFL.PanelSectionRow, { children: SP_JSX.jsx(DFL.ButtonItem, { layout: "below", onClick: handleGenerateWarp, disabled: loadingWarp, children: loadingWarp ? t.generatingWarp : t.generateWarp }) })] }))] }));
};
var index = definePlugin(() => {
    return {
        name: "Zapret & WARP",
        titleView: SP_JSX.jsx("div", { className: DFL.staticClasses.Title, children: "Zapret & WARP" }),
        content: SP_JSX.jsx(Content, {}),
        icon: SP_JSX.jsx(FaShieldAlt, {}),
        onDismount() {
            // Очистка
        },
    };
});

export { index as default };
//# sourceMappingURL=index.js.map

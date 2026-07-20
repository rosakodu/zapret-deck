import {
  ButtonItem,
  DialogBody,
  DialogButton,
  DialogFooter,
  DialogHeader,
  ModalRoot,
  PanelSection,
  PanelSectionRow,
  showModal,
  staticClasses,
  TextField,
  DropdownItem,
} from "@decky/ui";
import {
  callable,
  definePlugin,
  toaster,
} from "@decky/api";
import { useState, useEffect, useCallback, useMemo } from "react";
import { FaShieldAlt } from "react-icons/fa";

interface StatusInfo {
  mode: string;
  zapret_active: boolean;
  warp_active: boolean;
  warp_registered: boolean;
  autotune_in_progress: boolean;
  current_strategy: string;
}

interface StrategyInfo {
  name: string;
  args: string;
}

const getStatus = callable<[], StatusInfo>("get_status");
const setMode = callable<[string], { success: boolean; mode?: string; error?: string }>("set_mode");
const getStrategies = callable<[], StrategyInfo[]>("get_strategies");
const applyStrategy = callable<[string], { success: boolean; strategy?: string }>("apply_strategy");
const generateWarp = callable<[], { success: boolean }>("generate_warp");
const getHostlist = callable<[], string>("get_hostlist");
const saveHostlist = callable<[string], { success: boolean; error?: string }>("save_hostlist");
const startAutotune = callable<[], { success: boolean; error?: string }>("start_autotune");
const getSteamLanguage = callable<[], string>("get_steam_language");

type TranslationKeys =
  | "pluginTitle"
  | "modeTitle"
  | "modeOff"
  | "modeZapret"
  | "modeWarp"
  | "statusTitle"
  | "statusActive"
  | "statusInactive"
  | "zapretSettings"
  | "warpSettings"
  | "strategySelect"
  | "runAutotune"
  | "autotuneRunning"
  | "editHostlist"
  | "hostlistTitle"
  | "hostlistPlaceholder"
  | "save"
  | "cancel"
  | "warpStatus"
  | "warpRegistered"
  | "warpNotRegistered"
  | "generateWarp"
  | "generatingWarp"
  | "success"
  | "error"
  | "noWorkingStrategy"
  | "autotuneComplete"
  | "appliedStrategy";

const translations: Record<string, Record<TranslationKeys, string>> = {
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

const HostlistModal = ({
  closeModal,
  onSave,
  currentHosts,
  t,
}: {
  closeModal: () => void;
  onSave: (hosts: string) => void;
  currentHosts: string;
  t: Record<TranslationKeys, string>;
}) => {
  const [hosts, setHosts] = useState(currentHosts);

  return (
    <ModalRoot>
      <DialogHeader>{t.hostlistTitle}</DialogHeader>
      <DialogBody>
        <TextField
          label={t.hostlistPlaceholder}
          value={hosts}
          onChange={(e) => setHosts(e.target.value)}
        />
      </DialogBody>
      <DialogFooter>
        <DialogButton onClick={closeModal}>{t.cancel}</DialogButton>
        <DialogButton
          onClick={() => {
            onSave(hosts);
            closeModal();
          }}
        >
          {t.save}
        </DialogButton>
      </DialogFooter>
    </ModalRoot>
  );
};

const Content = () => {
  const [status, setStatus] = useState<StatusInfo | null>(null);
  const [strategies, setStrategies] = useState<StrategyInfo[]>([]);
  const [lang, setLang] = useState<string>("english");
  const [hostlist, setHostlist] = useState<string>("");
  const [loadingWarp, setLoadingWarp] = useState<boolean>(false);

  const t = useMemo(() => {
    return translations[lang] || translations.english;
  }, [lang]);

  const refreshStatus = useCallback(async () => {
    try {
      const res = await getStatus();
      setStatus(res);
    } catch (e) {
      console.error("Failed to get status", e);
    }
  }, []);

  useEffect(() => {
    refreshStatus();
    const interval = setInterval(refreshStatus, 3000);
    
    getSteamLanguage().then((l) => setLang(l || "english")).catch(() => setLang("english"));
    getStrategies().then((strats) => setStrategies(strats || [])).catch(() => setStrategies([]));
    getHostlist().then((hosts) => setHostlist(hosts || "")).catch(() => setHostlist(""));

    return () => clearInterval(interval);
  }, [refreshStatus]);

  const handleModeChange = async (mode: string) => {
    try {
      const res = await setMode(mode);
      if (res.success) {
        toaster.toast({
          title: t.pluginTitle,
          body: `${t.modeTitle}: ${mode === "off" ? t.modeOff : mode === "zapret" ? t.modeZapret : t.modeWarp}`,
        });
      } else {
        toaster.toast({
          title: t.error,
          body: res.error || "Failed to switch mode",
        });
      }
      refreshStatus();
    } catch (e) {
      console.error(e);
    }
  };

  const handleStrategyChange = async (args: string) => {
    try {
      const res = await applyStrategy(args);
      if (res.success) {
        toaster.toast({
          title: t.success,
          body: t.appliedStrategy,
        });
      }
      refreshStatus();
    } catch (e) {
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
      } else {
        toaster.toast({
          title: t.error,
          body: "Failed to generate WARP account",
        });
      }
      refreshStatus();
    } catch (e) {
      console.error(e);
    } finally {
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
      } else {
        toaster.toast({
          title: t.error,
          body: res.error || "Failed to start autotune",
        });
      }
      refreshStatus();
    } catch (e) {
      console.error(e);
    }
  };

  const handleEditHostlist = () => {
    showModal(
      <HostlistModal
        closeModal={() => {}}
        onSave={async (hosts) => {
          setHostlist(hosts);
          const res = await saveHostlist(hosts);
          if (res.success) {
            toaster.toast({
              title: t.success,
              body: t.appliedStrategy,
            });
          }
        }}
        currentHosts={hostlist}
        t={t}
      />
    );
  };

  if (!status) {
    return <PanelSection><PanelSectionRow>Loading...</PanelSectionRow></PanelSection>;
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

  return (
    <PanelSection title={t.pluginTitle}>
      <PanelSectionRow>
        <DropdownItem
          label={t.modeTitle}
          rgOptions={modeOptions}
          selectedOption={status.mode}
          onChange={(opt) => handleModeChange(opt.data)}
        />
      </PanelSectionRow>

      <PanelSectionRow>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span>{t.statusTitle}</span>
          <span style={{ color: isServiceActive ? "#4caf50" : "#f44336", fontWeight: "bold" }}>
            {isServiceActive ? t.statusActive : t.statusInactive}
          </span>
        </div>
      </PanelSectionRow>

      {status.mode === "zapret" && (
        <PanelSection title={t.zapretSettings}>
          <PanelSectionRow>
            <DropdownItem
              label={t.strategySelect}
              rgOptions={strategyOptions}
              selectedOption={status.current_strategy}
              onChange={(opt) => handleStrategyChange(opt.data)}
            />
          </PanelSectionRow>
          
          <PanelSectionRow>
            <ButtonItem
              layout="below"
              onClick={handleStartAutotune}
              disabled={status.autotune_in_progress}
            >
              {status.autotune_in_progress ? t.autotuneRunning : t.runAutotune}
            </ButtonItem>
          </PanelSectionRow>

          <PanelSectionRow>
            <ButtonItem layout="below" onClick={handleEditHostlist}>
              {t.editHostlist}
            </ButtonItem>
          </PanelSectionRow>
        </PanelSection>
      )}

      {status.mode === "warp" && (
        <PanelSection title={t.warpSettings}>
          <PanelSectionRow>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span>{t.warpStatus}</span>
              <span style={{ color: status.warp_registered ? "#4caf50" : "#ff9800", fontWeight: "bold" }}>
                {status.warp_registered ? t.warpRegistered : t.warpNotRegistered}
              </span>
            </div>
          </PanelSectionRow>

          <PanelSectionRow>
            <ButtonItem
              layout="below"
              onClick={handleGenerateWarp}
              disabled={loadingWarp}
            >
              {loadingWarp ? t.generatingWarp : t.generateWarp}
            </ButtonItem>
          </PanelSectionRow>
        </PanelSection>
      )}
    </PanelSection>
  );
};

export default definePlugin((serverApi: any) => {
  return {
    title: <div className={staticClasses.Title}>Zapret & WARP</div>,
    content: <Content />,
    icon: <FaShieldAlt />,
  };
});

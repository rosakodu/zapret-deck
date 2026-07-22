import {
  ButtonItem,
  PanelSection,
  PanelSectionRow,
  staticClasses,
} from "@decky/ui";
import {
  callable,
  definePlugin,
  toaster,
} from "@decky/api";
import { useState, useEffect, useCallback, useMemo, useRef } from "react";
import { FaShieldAlt } from "react-icons/fa";

interface StatusInfo {
  zapret_enabled: boolean;
  warp_enabled: boolean;
  zapret_active: boolean;
  warp_active: boolean;
  warp_registered: boolean;
  autotune_in_progress: boolean;
  current_strategy: string;
  current_strategy_name: string;
}

interface StrategyInfo {
  name: string;
  args: string;
}

const getStatus = callable<[], StatusInfo>("get_status");
const setServiceState = callable<[string, boolean], { success: boolean; service?: string; enabled?: boolean; error?: string }>("set_service_state");
const getStrategies = callable<[], StrategyInfo[]>("get_strategies");
const applyStrategy = callable<[string], { success: boolean; strategy?: string }>("apply_strategy");
const generateWarp = callable<[], { success: boolean }>("generate_warp");
const startAutotune = callable<[], { success: boolean; error?: string }>("start_autotune");
const getSteamLanguage = callable<[], string>("get_steam_language");
const updateResources = callable<[], { success: boolean; updated_lists: number }>("update_resources");

type TranslationKeys =
  | "pluginTitle"
  | "zapretTitle"
  | "warpTitle"
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
  | "appliedStrategy"
  | "updateResources"
  | "updating"
  | "language";

const translations: Record<string, Record<TranslationKeys, string>> = {
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

// Редактор списка сайтов убран

const Content = () => {
  const [status, setStatus] = useState<StatusInfo | null>(null);
  const [strategies, setStrategies] = useState<StrategyInfo[]>([]);
  const [lang, setLang] = useState<string>("english");
  const [loadingWarp, setLoadingWarp] = useState<boolean>(false);
  const [updatingResources, setUpdatingResources] = useState<boolean>(false);
  const [strategiesExpanded, setStrategiesExpanded] = useState<boolean>(false);

  const t = useMemo(() => {
    return translations[lang] || translations.english;
  }, [lang]);

  const refreshStatus = useCallback(async () => {
    try {
      const res = await getStatus();
      setStatus(res);
      const strats = await getStrategies();
      setStrategies(strats || []);
    } catch (e) {
      console.error("Failed to get status", e);
    }
  }, []);

  const prevInProgress = useRef<boolean>(false);

  useEffect(() => {
    if (status) {
      if (prevInProgress.current && !status.autotune_in_progress) {
        // Автоподбор только что завершился!
        if (status.zapret_enabled || status.current_strategy) {
          const stratName = status.current_strategy_name || "Авто";
          toaster.toast({
            title: t.pluginTitle,
            body: `${t.autotuneComplete} ${t.appliedStrategy}: ${stratName}`,
          });
        } else {
          toaster.toast({
            title: t.error,
            body: t.noWorkingStrategy || "Не найдено подходящих стратегий",
          });
        }
      }
      prevInProgress.current = status.autotune_in_progress;
    }
  }, [status, t]);

  useEffect(() => {
    refreshStatus();
    const interval = setInterval(refreshStatus, 3000);
    
    getSteamLanguage().then((l) => setLang(l || "english")).catch(() => setLang("english"));

    return () => clearInterval(interval);
  }, [refreshStatus]);

  const handleServiceToggle = async (service: string, enabled: boolean) => {
    try {
      const res = await setServiceState(service, enabled);
      if (res.success) {
        toaster.toast({
          title: t.pluginTitle,
          body: `${service === "zapret" ? t.zapretTitle : t.warpTitle}: ${enabled ? t.statusActive : t.statusInactive}`,
        });
      } else {
        toaster.toast({
          title: t.error,
          body: res.error || "Failed to toggle service",
        });
      }
      refreshStatus();
    } catch (e) {
      console.error(e);
    }
  };

  const handleStrategyChange = async (args: string, isSelected: boolean) => {
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

  const handleUpdateResources = async () => {
    setUpdatingResources(true);
    try {
      const res = await updateResources();
      if (res.success) {
        toaster.toast({
          title: t.pluginTitle,
          body: `${t.updateResources}: ${t.success}`,
        });
      } else {
        toaster.toast({
          title: t.error,
          body: "Failed to update resources",
        });
      }
    } catch (e) {
      console.error(e);
    } finally {
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
          } catch (err) {
            console.error(err);
          }
        }, 500);
      } else {
        toaster.toast({
          title: t.error,
          body: res.error || "Failed to start autotune",
        });
      }
    } catch (e) {
      console.error(e);
    }
  };

  if (!status) {
    return <PanelSection><PanelSectionRow>Loading...</PanelSectionRow></PanelSection>;
  }

  const isZapretActive = Boolean(!status.autotune_in_progress && (status.zapret_enabled || status.zapret_active));
  const isWarpActive = Boolean(status.warp_enabled || status.warp_active);

  return (
    <PanelSection>
      {/* Zapret Bypass Section */}
      <PanelSectionRow>
        <ButtonItem
          layout="below"
          onClick={() => handleServiceToggle("zapret", !isZapretActive)}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", width: "100%" }}>
            <span style={{ fontWeight: "normal", color: "inherit" }}>
              {t.zapretTitle}
            </span>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <span style={{ fontSize: "12px", color: isZapretActive ? "#1a9fff" : "#888", fontWeight: "bold" }}>
                {isZapretActive ? t.statusActive : t.statusInactive}
              </span>
              <div style={{
                width: "36px",
                height: "20px",
                borderRadius: "10px",
                backgroundColor: isZapretActive ? "#1a9fff" : "#3a3a3a",
                position: "relative",
                transition: "background-color 0.2s ease",
                display: "flex",
                alignItems: "center",
                padding: "2px",
                boxSizing: "border-box"
              }}>
                <div style={{
                  width: "16px",
                  height: "16px",
                  borderRadius: "50%",
                  backgroundColor: "#ffffff",
                  transform: isZapretActive ? "translateX(16px)" : "translateX(0px)",
                  transition: "transform 0.2s ease"
                }} />
              </div>
            </div>
          </div>
        </ButtonItem>
      </PanelSectionRow>

      <div style={{ display: "flex", justifyContent: "center", width: "100%", padding: "12px 0 6px 0" }}>
        <span style={{ fontSize: "11px", fontWeight: "bold", color: "#a5a5a5", textTransform: "uppercase", letterSpacing: "0.5px" }}>
          {t.zapretSettings}
        </span>
      </div>

      <PanelSectionRow>
        <ButtonItem
          layout="below"
          onClick={() => setStrategiesExpanded(!strategiesExpanded)}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", width: "100%" }}>
            <span style={{ fontWeight: "bold", color: "#a5a5a5", fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.5px" }}>
              {t.strategySelect}
            </span>
            <span style={{ fontSize: "10px", color: "#888" }}>
              {strategiesExpanded ? "▼" : "▶"}
            </span>
          </div>
        </ButtonItem>
      </PanelSectionRow>

      {strategiesExpanded && (
        <div style={{ maxHeight: "200px", overflowY: "auto", paddingRight: "4px", marginBottom: "8px", border: "1px solid #333", borderRadius: "4px", padding: "4px" }}>
          {strategies.map((s, idx) => {
            const isSelected = status.current_strategy_name === s.name.replace(" (Auto)", "");
            return (
              <PanelSectionRow key={idx}>
                <div style={{ position: "relative", width: "100%" }}>
                  <ButtonItem
                    layout="below"
                    onClick={() => handleStrategyChange(s.args, isSelected)}
                  >
                    <div style={{ display: "flex", alignItems: "center", width: "100%" }}>
                      <span style={{ fontWeight: isSelected ? "bold" : "normal", color: isSelected ? "#1a9fff" : "inherit" }}>
                        {s.name}
                      </span>
                    </div>
                  </ButtonItem>
                  {isSelected && (
                    <div style={{
                      position: "absolute",
                      top: 0,
                      left: 0,
                      right: 0,
                      bottom: 0,
                      border: "1.5px solid #1a9fff",
                      borderRadius: "4px",
                      pointerEvents: "none",
                      backgroundColor: "rgba(26, 159, 255, 0.1)"
                    }} />
                  )}
                </div>
              </PanelSectionRow>
            );
          })}
        </div>
      )}
      
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
        <ButtonItem
          layout="below"
          onClick={handleUpdateResources}
          disabled={updatingResources}
        >
          {updatingResources ? t.updating : t.updateResources}
        </ButtonItem>
      </PanelSectionRow>

      {/* WARP VPN Section */}
      <PanelSectionRow>
        <ButtonItem
          layout="below"
          onClick={() => handleServiceToggle("warp", !isWarpActive)}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", width: "100%" }}>
            <span style={{ fontWeight: "normal", color: "inherit" }}>
              {t.warpTitle}
            </span>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <span style={{ fontSize: "12px", color: isWarpActive ? "#1a9fff" : "#888", fontWeight: "bold" }}>
                {isWarpActive ? t.statusActive : t.statusInactive}
              </span>
              <div style={{
                width: "36px",
                height: "20px",
                borderRadius: "10px",
                backgroundColor: isWarpActive ? "#1a9fff" : "#3a3a3a",
                position: "relative",
                transition: "background-color 0.2s ease",
                display: "flex",
                alignItems: "center",
                padding: "2px",
                boxSizing: "border-box"
              }}>
                <div style={{
                  width: "16px",
                  height: "16px",
                  borderRadius: "50%",
                  backgroundColor: "#ffffff",
                  transform: isWarpActive ? "translateX(16px)" : "translateX(0px)",
                  transition: "transform 0.2s ease"
                }} />
              </div>
            </div>
          </div>
        </ButtonItem>
      </PanelSectionRow>

      <div style={{ display: "flex", justifyContent: "center", width: "100%", padding: "12px 0 6px 0" }}>
        <span style={{ fontSize: "11px", fontWeight: "bold", color: "#a5a5a5", textTransform: "uppercase", letterSpacing: "0.5px" }}>
          {t.warpSettings}
        </span>
      </div>

      <PanelSectionRow>
        <ButtonItem layout="below">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", width: "100%" }}>
            <span>{t.warpStatus}</span>
            <span style={{ color: status.warp_registered ? "#4caf50" : "#ff9800", fontWeight: "bold", fontSize: "12px" }}>
              {status.warp_registered ? t.warpRegistered : t.warpNotRegistered}
            </span>
          </div>
        </ButtonItem>
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
  );
};

export default definePlugin(() => {
  return {
    name: "Zapret Deck",
    titleView: <div className={staticClasses.Title}>Zapret Deck</div>,
    content: <Content />,
    icon: <FaShieldAlt />,
    onDismount() {
      // Очистка
    },
  };
});

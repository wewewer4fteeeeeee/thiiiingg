// @ts-nocheck
const api = "https://explodingcar.pythonanywhere.com/"
const keepAlive = [];

Il2Cpp.perform(() => {
    console.log("[Explodings version swapper] made by exploding car :3");
    
    try {
        const asm = Il2Cpp.domain.assembly("AnimalCompany");
        if (!asm) { 
            return; 
        }

        const getGameDataUrl = (version) => {
            const versionMap = {
                "1.70+": "https://ac-main.b-cdn.net/data/game-data-prod2.zip",
                "1.60-1.70": "https://raw.githubusercontent.com/wewewer4fteeeeeee/thiiiingg/refs/heads/main/1.60-1.70.zip",
                "1.56.0": "https://raw.githubusercontent.com/wewewer4fteeeeeee/thiiiingg/refs/heads/main/crafting.zip",
                "1.50.3": "https://raw.githubusercontent.com/wewewer4fteeeeeee/thiiiingg/refs/heads/main/1.53.3.zip",
                "1.40-1.51.0": "https://raw.githubusercontent.com/wewewer4fteeeeeee/thiiiingg/refs/heads/main/1.40-1.51.0.zip",
                "1.30-1.39": "https://raw.githubusercontent.com/wewewer4fteeeeeee/thiiiingg/refs/heads/main/1.30-1.39.zip",
                "1.20-1.30": "https://raw.githubusercontent.com/wewewer4fteeeeeee/thiiiingg/refs/heads/main/1.20-.130.zip"
            };

            if (!version) return versionMap["1.56.0"];

            const versionNum = parseFloat(version);
            
            if (versionNum >= 1.70) return versionMap["1.70+"];
            if (versionNum >= 1.60 && versionNum < 1.70) return versionMap["1.60-1.70"];
            if (versionNum === 1.56) return versionMap["1.56.0"];
            if (versionNum === 1.50) return versionMap["1.50.3"];
            if (versionNum >= 1.40 && versionNum < 1.52) return versionMap["1.40-1.51.0"];
            if (versionNum >= 1.30 && versionNum < 1.40) return versionMap["1.30-1.39"];
            if (versionNum >= 1.20 && versionNum < 1.30) return versionMap["1.20-1.30"];
            
            return versionMap["1.56.0"];
        };

        let gameDataUrl = "";

        const tryFieldPatch = (obj, fieldName) => {
            try { 
                const field = obj.field(fieldName);
                if (field && !field.isNull()) {
                    const newUrl = Il2Cpp.string(gameDataUrl);
                    field.value = newUrl;
                    return true;
                }
            } catch (e) {}
            return false;
        };

        const patchApiOrigin = (obj) => {
            try { 
                const field = obj.field("_apiOrigin");
                if (field && !field.isNull()) {
                    const newUrl = Il2Cpp.string(api);
                    field.value = newUrl;
                    return true;
                }
            } catch (e) {}
            return false;
        };

        try {
            const acs = asm.image.class("AnimalCompany.AntiCheatSystem");
            const awake = acs.tryMethod("Awake");
            if (awake) {
                Interceptor.attach(awake.virtualAddress, {
                    onEnter(args) {
                        const self = new Il2Cpp.Object(args[0]);
                        try { self.field("_vpnDetector").value = Il2Cpp.Object.zero; } catch(e) {}
                        try { self.field("_fridaDetector").value = Il2Cpp.Object.zero; } catch(e) {}
                    }
                });
            }
            const acUpdate = acs.tryMethod("Update");
            if (acUpdate) {
                Interceptor.replace(acUpdate.virtualAddress, new NativeCallback(() => {}, 'void', []));
            }
        } catch(e) {}

        try {
            const vpn = asm.image.class("AnimalCompany.VPNDetector");
            const checkVPN = vpn.tryMethod("CheckVPNIsActive");
            if (checkVPN) {
                Interceptor.attach(checkVPN.virtualAddress, {
                    onLeave(retval) { retval.replace(Il2Cpp.Boolean(false).handle); }
                });
            }
            const vpnUpdate = vpn.tryMethod("Update");
            if (vpnUpdate) {
                Interceptor.replace(vpnUpdate.virtualAddress, new NativeCallback(() => {}, 'void', []));
            }
            const vpnCtor = vpn.tryMethod(".ctor");
            if (vpnCtor) {
                Interceptor.attach(vpnCtor.virtualAddress, {
                    onEnter(args) {
                        try {
                            const intervalField = vpn.field("POLL_INTERVAL");
                            if (intervalField) intervalField.value = Il2Cpp.Single(999999);
                        } catch(e) {}
                    }
                });
            }
        } catch(e) {}

        try {
            const frida = asm.image.class("AnimalCompany.FridaDetector");
            const getFrida = frida.tryMethod("get_isFridaDetected");
            if (getFrida) {
                Interceptor.attach(getFrida.virtualAddress, {
                    onLeave(retval) { retval.replace(Il2Cpp.Boolean(false).handle); }
                });
            }
            const fridaUpdate = frida.tryMethod("Update");
            if (fridaUpdate) {
                Interceptor.replace(fridaUpdate.virtualAddress, new NativeCallback(() => {}, 'void', []));
            }
            const portCheck = frida.tryMethod("IsFridaPortOpen");
            if (portCheck) {
                Interceptor.attach(portCheck.virtualAddress, {
                    onLeave(retval) { retval.replace(Il2Cpp.Boolean(false).handle); }
                });
            }
        } catch(e) {}

        try {
            const AS = asm.image.class("AnimalCompany.AppStartup");
            const gc = AS.tryMethod("GetAppStartupConfig");
            if (gc) {
                Interceptor.attach(gc.virtualAddress, {
                    onEnter(args) { this.p = args[gc.parameterCount === 7 ? 4 : 3]; },
                    onLeave(retval) {
                        try { 
                            this.p.writePointer(Il2Cpp.string(api)); 
                        } catch(e) {}
                    }
                });
            }
        } catch(e) {}

        let appStartupInstance = null;

        try {
            const AS = asm.image.class("AnimalCompany.AppStartup");
            for (const name of ["Awake", "Start"]) {
                const m = AS.tryMethod(name, 0);
                if (!m) continue;
                Interceptor.attach(m.virtualAddress, {
                    onEnter(args) { 
                        this.self = new Il2Cpp.Object(args[0]);
                        appStartupInstance = this.self;
                    },
                    onLeave(args) { 
                        patchApiOrigin(this.self);
                        if (gameDataUrl) {
                            const field = this.self.field("_gameDataURL");
                            if (field) {
                                field.value = Il2Cpp.string(gameDataUrl);
                            }
                        }
                    }
                });
            }
        } catch(e) {}

        try {
            const IA = asm.image.class("AnimalCompany.InitializeAppAction");
            const ctor = IA.tryMethod(".ctor");
            if (ctor) {
                Interceptor.attach(ctor.virtualAddress, {
                    onEnter(args) { 
                        this.self = new Il2Cpp.Object(args[0]);
                        try {
                            const versionField = this.self.field("_clientVersion");
                            if (versionField && versionField.value) {
                                const version = versionField.value.content;
                                console.log(`[clientVersion] = ${version}`);
                                gameDataUrl = getGameDataUrl(version);
                                console.log(`[gameDataURL] = ${gameDataUrl}`);
                            }
                        } catch(e) {}
                    },
                    onLeave(retval) { 
                        patchApiOrigin(this.self);
                        if (gameDataUrl) {
                            const field = this.self.field("_gameDataURL");
                            if (field) {
                                field.value = Il2Cpp.string(gameDataUrl);
                            }
                        }
                    }
                });
            }
            const exec = IA.tryMethod("Execute", 1);
            if (exec) {
                Interceptor.attach(exec.virtualAddress, {
                    onEnter(args) { 
                        this.self = new Il2Cpp.Object(args[0]);
                        try {
                            const versionField = this.self.field("_clientVersion");
                            if (versionField && versionField.value) {
                                const version = versionField.value.content;
                                console.log(`[clientVersion] = ${version}`);
                                gameDataUrl = getGameDataUrl(version);
                                console.log(`[gameDataURL] = ${gameDataUrl}`);
                            }
                        } catch(e) {}
                    },
                    onLeave(retval) { 
                        patchApiOrigin(this.self);
                        if (gameDataUrl) {
                            const field = this.self.field("_gameDataURL");
                            if (field) {
                                field.value = Il2Cpp.string(gameDataUrl);
                            }
                        }
                    }
                });
            }
        } catch(e) {}

        try {
            const appFlags = asm.image.class("AnimalCompany.AppFlags");
            if (appFlags) {
                for (const methodName of ["get_isHalloween","get_isThanksgiving","get_isSnowStorm","get_isHeavyRain"]) {
                    try {
                        const method = appFlags.tryMethod(methodName);
                        if (method) {
                            Interceptor.attach(method.virtualAddress, {
                                onLeave(retval) { try { retval.value = false; } catch(e) {} }
                            });
                        }
                    } catch(e) {}
                }
            }
        } catch(e) {}

        try {
            const seasonalEventManager = asm.image.class("AnimalCompany.SeasonalEventManager");
            if (seasonalEventManager) {
                for (const methodName of ["get_isSnowStormActive","get_isHeavyRainActive"]) {
                    try {
                        const method = seasonalEventManager.tryMethod(methodName);
                        if (method) {
                            Interceptor.attach(method.virtualAddress, {
                                onLeave(retval) { try { retval.value = false; } catch(e) {} }
                            });
                        }
                    } catch(e) {}
                }
                try {
                    const instance = seasonalEventManager.field("instance");
                    if (instance) {
                        const inst = instance.value;
                        if (inst) {
                            const self = new Il2Cpp.Object(inst);
                            for (const fname of ["_isSnowStormActive","_isHeavyRainActive"]) {
                                try { const f = self.field(fname); if (f) f.value = Il2Cpp.Boolean(false); } catch(e) {}
                            }
                            for (const fname of ["_snowStormAudioSource","_heavyRainAudioSource"]) {
                                try {
                                    const af = self.field(fname);
                                    if (af) { const a = af.value; if (a) { const v = a.field("volume"); if (v) v.value = Il2Cpp.Single(0); } }
                                } catch(e) {}
                            }
                        }
                    }
                } catch(e) {}
            }
        } catch(e) {}

        try {
            const AS = asm.image.class("AnimalCompany.AppStartup");
            const fetchMethod = AS.tryMethod("FetchAndLoadGameDataCommand");
            if (fetchMethod) {
                Interceptor.attach(fetchMethod.virtualAddress, {
                    onEnter(args) {
                        if (appStartupInstance && gameDataUrl) {
                            const field = appStartupInstance.field("_gameDataURL");
                            if (field) {
                                field.value = Il2Cpp.string(gameDataUrl);
                            }
                            const apiField = appStartupInstance.field("_apiOrigin");
                            if (apiField) {
                                apiField.value = Il2Cpp.string(api);
                            }
                        }
                    },
                    onLeave(retval) {
                        if (appStartupInstance && gameDataUrl) {
                            const field = appStartupInstance.field("_gameDataURL");
                            if (field) {
                                field.value = Il2Cpp.string(gameDataUrl);
                            }
                            const apiField = appStartupInstance.field("_apiOrigin");
                            if (apiField) {
                                apiField.value = Il2Cpp.string(api);
                            }
                        }
                    }
                });
            }
        } catch(e) {}

        try {
            const apiClass = asm.image.class("AnimalCompany.API.AnimalCompanyAPI");
            if (apiClass) {
                const bootstrapMethod = apiClass.tryMethod("BootstrapAsync");
                if (bootstrapMethod) {
                    Interceptor.attach(bootstrapMethod.virtualAddress, {
                        onEnter(args) {},
                        onLeave(retval) {
                            if (gameDataUrl) {
                                try {
                                    if (retval && !retval.isNull()) {
                                        const response = new Il2Cpp.Object(retval);
                                        const gameDataField = response.field("gameDataURL");
                                        if (gameDataField) {
                                            gameDataField.value = Il2Cpp.string(gameDataUrl);
                                        }
                                    }
                                } catch(e) {}
                            }
                        }
                    });
                }
            }
        } catch(e) {}

    } catch(e) {}
});

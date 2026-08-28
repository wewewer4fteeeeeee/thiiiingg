declare const Il2Cpp: any;
declare const System: any;
declare const XRNode: any;
declare const Random: any;
declare const UnityEngine: any;

let rigidbody: any = null
let hue = 0;
let lastRunTime = 0;

let tagGunDelay = 0;

let buttonClickDelay = 0.0;
let menu: any = null;
let reference: any = null;
let referenceCollider: any = null;

let leftPrimary = false;
let leftSecondary = false;

let colorIndex = 0;
let perviousTeleportKey = false;
let colorDelay = 0;

let rightPrimary = false;
let rightSecondary = false;

let leftGrab = false;
let rightGrab = false;

let leftTrigger = false;
let rightTrigger = false;

let deltaTime = 0.0;
let time = 0.0;
let itemIndex = 0;
let teleIndex = 0;
let previousNoclipKey = false;
let perviousDestroyKey = false;

let bgColor: [number, number, number, number] = [0.0, 0.0, 0.0, 1.0];
let bgColor2: [number, number, number, number] = [9.0, 9.0, 9.0, 1.0];
let textColor: [number, number, number, number] = [1.0, 1.0, 1.0, 1.0];
let buttonColor: [number, number, number, number] = [0.1, 0.1, 0.1, 1.0];
let buttonPressedColor: [number, number, number, number] = [0.7, 0.7, 0.7, 1.0];
let itemIDs: string[] = [];
let itemPrefabHandles: any[] = [];
let prefabListReady = false;
let spawnDelegate: any = null;

let pidMapCache: number[] | null = null;
let pidMapTable: any = null;
let pidDumping = false;

if (!(globalThis as any).__abortHooked) {
    (globalThis as any).__abortHooked = true;
}



let menuName: string = "J0ker Client";
let themeIndex = 0;
class XRInputHandler {
  private InputDevices: any;
  private tryGetFeatureValue: any;
  private buttonStates: Map<string, boolean>;

  constructor() {
    this.InputDevices = Il2Cpp.domain
      .assembly("UnityEngine.XRModule")
      .image.class("UnityEngine.XR.InputDevices");

    this.tryGetFeatureValue = this.InputDevices.method("TryGetFeatureValue_bool", 3);
    this.buttonStates = new Map();
  }

  update() {
    this.updateControllerStates(1); // left controller
    this.updateControllerStates(2); // right controller
  }

  private updateControllerStates(controllerId: number) {
    const features = [
      "PrimaryButton",
      "SecondaryButton",
      "GripButton",
      "TriggerButton",
      "MenuButton"
    ];

    features.forEach(feature => {
      const key = `${controllerId}_${feature}`;
      this.buttonStates.set(key, this.getButtonState(controllerId, feature));
    });
  }

  private getButtonState(deviceId: number, featureName: string): boolean {
    try {
      const valuePtr = Il2Cpp.alloc(1);
      const feature = Il2Cpp.string(featureName);
      const success = this.tryGetFeatureValue.invoke(uint64(deviceId), feature, valuePtr);
      if (success) {
        return valuePtr.readU8() !== 0;
      }
    } catch (_) { }
    return false;
  }

  isButtonPressed(controllerId: number, feature: string): boolean {
    return this.buttonStates.get(`${controllerId}_${feature}`) || false;
  }

  get leftControllerPrimaryButton(): boolean { return this.isButtonPressed(1, "PrimaryButton"); }
  get leftControllerSecondaryButton(): boolean { return this.isButtonPressed(1, "SecondaryButton"); }
  get rightControllerPrimaryButton(): boolean { return this.isButtonPressed(2, "PrimaryButton"); }
  get rightControllerSecondaryButton(): boolean { return this.isButtonPressed(2, "SecondaryButton"); }
  get leftGrab(): boolean { return this.isButtonPressed(1, "GripButton"); }
  get rightGrab(): boolean { return this.isButtonPressed(2, "GripButton"); }
  get leftControllerTriggerButton(): boolean { return this.isButtonPressed(1, "TriggerButton"); }
  get rightControllerTriggerButton(): boolean { return this.isButtonPressed(2, "TriggerButton"); }
  get controllerMenuButton(): boolean {
    return this.isButtonPressed(1, "MenuButton") || this.isButtonPressed(2, "MenuButton");
  }
}

Il2Cpp.perform(() => {
  const images = {
    "AnimalCompany": Il2Cpp.domain.assembly("AnimalCompany").image,
    "UnityEngine.CoreModule": Il2Cpp.domain.assembly("UnityEngine.CoreModule").image,
    "UnityEngine.PhysicsModule": Il2Cpp.domain.assembly("UnityEngine.PhysicsModule").image,
    "UnityEngine.UIModule": Il2Cpp.domain.assembly("UnityEngine.UIModule").image,
    "UnityEngine.UI": Il2Cpp.domain.assembly("UnityEngine.UI").image,
    "UnityEngine": Il2Cpp.domain.assembly("UnityEngine").image,
    "UnityEngine.TextRenderingModule": Il2Cpp.domain.assembly("UnityEngine.TextRenderingModule").image,
  };

  const AssemblyCSharp = images["AnimalCompany"];
  const UnityEngineCore = images["UnityEngine.CoreModule"];
  const UnityEnginePhysics = images["UnityEngine.PhysicsModule"];
  const UnityEngineUI = images["UnityEngine.UI"];
  const UnityEngineUIModule = images["UnityEngine.UIModule"];
  const UnityEngineTextRendering = images["UnityEngine.TextRenderingModule"];
  const GameObject = UnityEngineCore.class("UnityEngine.GameObject");
  const Object = UnityEngineCore.class("UnityEngine.Object");
  const PrefabGen = AssemblyCSharp.class("AnimalCompany.PrefabGenerator");
  const NetPlayer = AssemblyCSharp.class("AnimalCompany.NetPlayer");
  const GBIClass = AssemblyCSharp.class("AnimalCompany.GrabbableItem");
  const Component = UnityEngineCore.class("UnityEngine.Component");
  const Vector3 = UnityEngineCore.class("UnityEngine.Vector3");
  const Quaternion = UnityEngineCore.class("UnityEngine.Quaternion");
  const Time = UnityEngineCore.class("UnityEngine.Time");
  const Resources = UnityEngineCore.class("UnityEngine.Resources");
  const Renderer = UnityEngineCore.class("UnityEngine.Renderer");
  const Shader = UnityEngineCore.class("UnityEngine.Shader");
  const RectTransform = UnityEngineCore.class("UnityEngine.RectTransform");
  const MeshCollider = UnityEnginePhysics.class("UnityEngine.Collider");
  const BoxCollider = UnityEnginePhysics.class("UnityEngine.BoxCollider");
  const Collider = UnityEnginePhysics.class("UnityEngine.Collider");
  const Rigidbody = UnityEnginePhysics.class("UnityEngine.Rigidbody");
  const Physics = UnityEnginePhysics.class("UnityEngine.Physics");
  const SystemObject = Il2Cpp.corlib.class("System.Object");

  const Canvas = UnityEngineUIModule.class("UnityEngine.Canvas");
  const CanvasScaler = UnityEngineUI.class("UnityEngine.UI.CanvasScaler");
  const GraphicRaycaster = UnityEngineUI.class("UnityEngine.UI.GraphicRaycaster");
  const Text = UnityEngineUI.class("UnityEngine.UI.Text");
  const Font = UnityEngineTextRendering.class("UnityEngine.Font");


function findLocomotionClass() {
        const classNames = [
            "AnimalCompany.GorillaLocomotion",
            "Assembly-CSharp.GorillaLocomotion",
            "AssemblyCSharp.GorillaLocomotion.GTPlayer",
            "GorillaLocomotion.Player",
            "GorillaLocomotion.Playerz",
            "j.Player",
            "j",
            "GorillaLocomotion1.Player",
            "GLocomotion.Player",
            "GTAGVrLocomotion.Player",
            "GTPlayer",
            "Player"

        ];
        for (const className of classNames) {
            const klass = AssemblyCSharp.tryClass(className);
            if (klass?.tryMethod("LateUpdate") || klass?.tryMethod("Update") || klass?.tryMethod("FixedUpdate") || klass?.tryMethod("OnLateUpdate")) {
                if (klass.tryField("_instance") || klass.tryMethod("get_Instance")) {
                    return klass;
                }
            }
        }
        for (const klass of AssemblyCSharp.classes) {
            const fullName = klass.fullName ?? "";
            const lowerName = fullName.toLowerCase();
            if (lowerName.includes("locomotion") && lowerName.includes("player") && 
                (klass.tryMethod("LateUpdate") || klass.tryMethod("Update") || klass.tryMethod("FixedUpdate") || klass.tryMethod("OnLateUpdate")) &&
                (klass.tryField("_instance") || klass.tryMethod("get_Instance"))) {
                return klass;
            }
        }
        throw new Error("Could not find a locomotion player class.");
    }

const GTPlayerClass = findLocomotionClass();
const GTPlayer = GTPlayerClass.method("get_Instance").invoke();

const GorillaTagger = GTPlayer;

  for (const field of GTPlayerClass.fields) {
    if (field.type.name == "UnityEngine.Rigidbody") {
      rigidbody = GTPlayer.field(field.name).value
    }
  }

  for (const field of GTPlayerClass.fields) {
    if (field.type.name == "UnityEngine.Rigidbody") {
      rigidbody = GTPlayer.field(field.name).value
    }
  }

  const MenuShader = Shader.method("Find").invoke(Il2Cpp.string("Universal Render Pipeline/Unlit"));
  const TextShader = Shader.method("Find").invoke(Il2Cpp.string("GUI/Text Shader"));

  const zeroVector = Vector3.field("zeroVector").value;
  const oneVector = Vector3.field("oneVector").value;
  const identityQuaternion = Quaternion.field("identityQuaternion").value;

  const leftHandTransform = GorillaTagger.field("leftHandTransform").value;
  const rightHandTransform = GorillaTagger.field("rightHandTransform").value;
  const headCollider = GorillaTagger.field("headCollider").value;
  let mutationName: string = "None";
  let ovrideBool: boolean;
  let infAmmoRevolverCock = false;

  const OVRInputHandler = new XRInputHandler();

  const arial = Resources
    .method("GetBuiltinResource", 1)
    .inflate(Font)
    .invoke(Il2Cpp.string("Arial.ttf"));

  function Destroy(object: any) {
    Object.method("Destroy", 1).invoke(object);
  }

const autofindclasscauselazyyesyes = (() => {
    let leclass = null;
    for (const assembly of Il2Cpp.domain.assemblies) {
        for (const klass of assembly.image.classes) {
            let hasthingygood = false, hasthingybad = false;
            for (const method of klass.methods) {
                if (method.name === "OnTriggerEnter") hasthingygood = true;
                if (method.name === "Awake") hasthingybad = true;
            }
            if (hasthingygood && !hasthingybad) {
                leclass = klass;
                break;
            }
        }
        if (leclass) break;
    }
    if (leclass) {
        return function() {
            return leclass;
        };
    } else {
        console.log("Oooh shoot");
        return function() {
            return null;
        };
    }
})();

const GorillaReportButton = autofindclasscauselazyyesyes();

console.log("menu trigger hook target: " + (GorillaReportButton ? GorillaReportButton.type.name : "none"));

  function getComponent(obj: any, type: any) {
    return obj.method("GetComponent", 1).inflate(type).invoke();
  }

  function addComponent(obj: any, type: any) {
    return obj.method("AddComponent", 1).inflate(type).invoke();
  }

  function getComponentInParent(obj: any, type: any) {
    return obj.method("GetComponentInParent", 0).inflate(type).invoke();
  }

  function getTransform(obj: any) {
    return obj.method("get_transform").invoke();
  }

  function hsl2Rgb(h: any, s: any, l: any) {
    s /= 100;
    l /= 100;
    const k = (n: any) => (n + h / 30) % 12;
    const a = s * Math.min(l, 1 - l);
    const f = (n: any) => l - a * Math.max(-1, Math.min(k(n) - 3, Math.min(9 - k(n), 1)));
    return [
      Math.round(255 * f(0)),
      Math.round(255 * f(8)),
      Math.round(255 * f(4))
    ];
  }

  function getSmoothColor() {
    hue = (hue + 0.5) % 360;
    const [r, g, b] = hsl2Rgb(hue, 100, 50);
    return { r: r / 255, g: g / 255, b: b / 255, a: 1.0 };
  }

  function randomInt(min: number, max: number) {
    return Math.floor(Math.random() * (max - min)) + min;
  }

  function renderMenuText(canvasObject: any, text: string = "", color: [number, number, number, number] = [1, 1, 1, 1], pos = zeroVector, size = oneVector) {
    const title = addComponent(createObject(zeroVector, identityQuaternion, oneVector, 3, [0, 0, 0, 0], getTransform(canvasObject)), Text);
    getComponent(title, BoxCollider).method("set_isTrigger").invoke(true);
    title.method("set_text").invoke(Il2Cpp.string(text));
    title.method("set_font").invoke(arial);
    title.method("set_fontSize").invoke(1);
    title.method("set_color").invoke(color);
    title.method("set_fontStyle").invoke(3);
    title.method("set_alignment").invoke(4);
    title.method("set_resizeTextForBestFit").invoke(true);
    title.method("set_resizeTextMinSize").invoke(0);

    const rectTransform = getComponent(title, RectTransform);
    rectTransform.method("set_sizeDelta").invoke(size);
    rectTransform.method("set_position").invoke(pos);
    rectTransform.method("set_rotation").invoke(Quaternion.method("Euler").invoke(180.0, 90.0, 90.0))
  }
  
  function createObject(
    pos = zeroVector,
    rot = identityQuaternion,
    scale = oneVector,
    primitiveType: number = 3,
    colorArr: [number, number, number, number] = [1, 1, 1, 1],
    parent = null
  ) {
    const obj = GameObject.method("CreatePrimitive").invoke(primitiveType);

    const renderer = getComponent(obj, Renderer);

    if (colorArr[3] == 0) {
      renderer.method("set_enabled").invoke(false);
    } else {
      const material = renderer.method("get_material").invoke();
      material.method("set_shader").invoke(MenuShader);
      material.method("set_color").invoke(colorArr);
    }

    const transform = getTransform(obj);
    if (parent != null) {
      transform.method("SetParent", 2).invoke(parent, false);
    }

    transform.method("set_position").invoke(pos);
    transform.method("set_rotation").invoke(rot);
    transform.method("set_localScale").invoke(scale);

    return obj;
  }

  function renderMenu() {
    menu = createObject(zeroVector, identityQuaternion, [0.1, 0.3, 0.3825], 3, [0, 0, 0, 0]);
    Destroy(getComponent(menu, BoxCollider))

    const menuBackground = createObject([0.1, 0, 0], identityQuaternion, [0.1, 0.86, 0.7], 3, bgColor, getTransform(menu))
    Destroy(getComponent(menuBackground, BoxCollider))

    const menuBackground2 = createObject([0.1, 0, 0], identityQuaternion, [0.09, 0.88, 0.72], 3, bgColor2, getTransform(menu))
    Destroy(getComponent(menuBackground2, BoxCollider))

    const canvasObject = createObject(zeroVector, identityQuaternion, oneVector, 3, [0, 0, 0, 0], getTransform(menu));
    const canvas = addComponent(canvasObject, Canvas);
    Destroy(getComponent(canvasObject, BoxCollider))

    const canvasScaler = addComponent(canvasObject, CanvasScaler);
    addComponent(canvasObject, GraphicRaycaster);
    canvas.method("set_renderMode").invoke(2);
    canvasScaler.method("set_dynamicPixelsPerUnit").invoke(1000.0);

    const homeButton = createObject([0.1, -0.06, 0.205], identityQuaternion, [0.09, 0.2682, 0.075], 3, buttonColor, getTransform(menu));
    const homeButton2 = createObject([0.1, -0.06, 0.205], identityQuaternion, [0.08, 0.3, 0.1], 3, bgColor2, getTransform(menu));
    homeButton.method("set_name").invoke(Il2Cpp.string("@Home"));

    addComponent(homeButton, GorillaReportButton);
    getComponent(homeButton, BoxCollider).method("set_isTrigger").invoke(true);

    renderMenuText(canvasObject, "Home", textColor, [0.105, -0.06, 0.205], [0.15, 0.15]);

    const leaveButton = createObject([0.1, 0.06, 0.205], identityQuaternion, [0.09, 0.2682, 0.075], 3, buttonColor, getTransform(menu));
    const leaveButton2 = createObject([0.1, 0.06, 0.205], identityQuaternion, [0.08, 0.3, 0.1], 3, bgColor2, getTransform(menu));
    leaveButton.method("set_name").invoke(Il2Cpp.string("@Leave"));

    addComponent(leaveButton, GorillaReportButton);
    getComponent(leaveButton, BoxCollider).method("set_isTrigger").invoke(true);

    renderMenuText(canvasObject, "Leave", textColor, [0.105, 0.06, 0.205], [0.15, 0.15]);
    renderMenuText(canvasObject, "linktr.ee/j0kermodz", textColor, [0.107, 0, -0.120], [.5, .5]);

    renderMenuText(canvasObject, menuName + ` - Page [ <color=cyan>${currentPage + 1} </color>]`, textColor, [0.11, 0, 0.155], [1, .1]);
    {
      const pageButton = createObject([0.1, 0.17, 0], identityQuaternion, [0.09, 0.15, 0.58], 3, buttonColor, getTransform(menu));
      const pageButton2 = createObject([0.1, 0.17, 0], identityQuaternion, [0.08, 0.16, 0.59], 3, bgColor2, getTransform(menu));
      pageButton.method("set_name").invoke(Il2Cpp.string("@PreviousPage"));


      addComponent(pageButton, GorillaReportButton);
      getComponent(pageButton, BoxCollider).method("set_isTrigger").invoke(true);
      renderMenuText(canvasObject, "?", textColor, [0.11, 0.17, 0], [1, 0.1]);
    }

    {
      const pageButton = createObject([0.1, -0.17, 0], identityQuaternion, [0.09, 0.15, 0.58], 3, buttonColor, getTransform(menu));
      const pageButton2 = createObject([0.1, -0.17, 0], identityQuaternion, [0.08, 0.16, 0.59], 3, bgColor2, getTransform(menu));
      pageButton.method("set_name").invoke(Il2Cpp.string("@NextPage"));


      addComponent(pageButton, GorillaReportButton);
      getComponent(pageButton, BoxCollider).method("set_isTrigger").invoke(true);
      renderMenuText(canvasObject, "?", textColor, [0.11, -0.17, 0], [1, 0.1]);
    }

    let i = 0;
    const targetMods = buttons[currentCategory]
      .slice(currentPage * 6)
      .slice(0, 6);


    targetMods.forEach((buttonData) => {
      const button = createObject([0.105, 0, 0.11 - (i * 0.04)], identityQuaternion, [0.09, 0.8, 0.08], 3, buttonColor, getTransform(menu));
      const button2 = createObject([0.105, 0, 0.11 - (i * 0.04)], identityQuaternion, [0.08, 0.82, 0.09], 3, bgColor2, getTransform(menu));

      button.method("set_name").invoke(Il2Cpp.string("@" + buttonData.buttonText));

      addComponent(button, GorillaReportButton);
      getComponent(button, BoxCollider).method("set_isTrigger").invoke(true);
      renderMenuText(canvasObject, buttonData.buttonText, textColor, [0.11, 0, 0.11 - (i * 0.04)], [1, 0.1]);
      updateButtonColor(button, buttonData);
      i++;
    });

    recenterMenu();
  }

  function renderReference() {
    reference = createObject(zeroVector, identityQuaternion, [0.01, 0.01, 0.01], 0, bgColor2, rightHandTransform)
    referenceCollider = getComponent(reference, Collider);

    getTransform(reference).method("set_localPosition").invoke([-0.02, 0.0010, 0.165]);
    reference.method("set_layer").invoke(2);
    addComponent(reference, Rigidbody).method("set_isKinematic").invoke(true);
  }

  let gunLocked = false;
  let lockTarget: any = null;
  let GunPointer: any = null;
  let GunLine: any = null;

  function renderGun(overrideLayerMask: any = null) {
    const StartPosition = rightHandTransform.method("get_position").invoke();
    const Direction = rightHandTransform.method("get_forward").invoke();

    const DirectionDivided = Vector3.method("op_Division").invoke(Direction, 4);
    const rayStartPosition = Vector3.method("op_Addition").invoke(StartPosition, DirectionDivided);

    const layerMask = overrideLayerMask || -3180559;

    const hits = Physics.method("RaycastAll", 4).invoke(rayStartPosition, Direction, 512.0, layerMask);
    let finalDistance = Infinity;
    let finalRay = null;
    for (const hit of hits) {
      const distance = Vector3.method("Distance").invoke(hit.method("get_point").invoke(), StartPosition);
      if (distance < finalDistance) {
        finalRay = hit;
        finalDistance = distance;
      }
    }

    let EndPosition;
    if (gunLocked) {
      EndPosition = getTransform(lockTarget).method("get_position").invoke();
    } else {
      EndPosition = finalRay.method("get_point").invoke();
    }

    if (Vector3.method("op_Equality").invoke(EndPosition, zeroVector)) {
      const farDirection = Vector3.method("op_Multiply").invoke(Direction, 512);
      EndPosition = Vector3.method("op_Addition").invoke(StartPosition, farDirection);
    }

    if (GunPointer == null) {
      GunPointer = createObject(EndPosition, identityQuaternion, [0.1, 0.1, 0.1], 0, [1, 1, 1, 1]);
    }

    GunPointer.method("SetActive").invoke(true);
    const pointerTransform = getTransform(GunPointer);
    pointerTransform.method("set_position").invoke(EndPosition);

    const PointerRenderer = getComponent(GunPointer, Renderer);
    const material = PointerRenderer.method("get_material").invoke();

    material.method("set_shader").invoke(TextShader);

    const pointerColor = (gunLocked || rightTrigger) ? buttonPressedColor : buttonColor;
    material.method("set_color").invoke(pointerColor);

    const collider = getComponent(GunPointer, Collider);
    if (collider != null) {
      Destroy(collider);
    }


    if (rightTrigger || gunLocked) {
      const Step = 10;
      for (let i = 1; i < (Step - 1); i++) {
        const t = i / (Step - 1);
        const Position = Vector3.method("Lerp").invoke(StartPosition, EndPosition, t);

        const randomValue = Math.random();
        let offset = zeroVector;

        if (randomValue > 0.75) {
          offset = [
            (Math.random() * 0.2) - 0.1,
            (Math.random() * 0.2) - 0.1,
            (Math.random() * 0.2) - 0.1
          ];
        }

      }

    }
    return { ray: finalRay, gunPointer: GunPointer };
  }

  function recenterMenu() {
    let menuPosition = leftHandTransform.method("get_position").invoke();
    let menuRotation = leftHandTransform.method("get_rotation").invoke();

    menuRotation = Quaternion.method("op_Multiply", 2).invoke(menuRotation, Quaternion.method("Euler").invoke(-45, 0, 0))

    const menuTransform = getTransform(menu);
    menuTransform.method("set_position").invoke(menuPosition);
    menuTransform.method("set_rotation").invoke(menuRotation);
  }

  function reloadMenu() {
    if (menu != null) {
      Object.method("Destroy", 1).invoke(menu);
      menu = null;
    }
  }

  function updateButtonColor(button: any, buttonData: any) {
    const RendererClass = Il2Cpp.domain
      .assembly("UnityEngine.CoreModule")
      .image
      .class("UnityEngine.Renderer");

    const renderer = getComponent(button, RendererClass);
    if (!renderer) {
      return;
    }

    const material = renderer.method("get_material").invoke();
    material.method("set_color").invoke(buttonData.enabled ? buttonPressedColor : buttonColor);
  }

  interface ButtonInfoConfig {
    buttonText: string;
    method?: () => void;
    enableMethod?: () => void;
    disableMethod?: () => void;
    keepOn?: boolean;
    enabled?: boolean;
  }

  class ButtonInfo {
    buttonText: string;
    method?: () => void;
    enableMethod?: () => void;
    disableMethod?: () => void;
    keepOn: boolean;
    enabled: boolean;

    constructor(config: ButtonInfoConfig) {
      this.buttonText = config.buttonText;
      this.method = config.method;
      this.enableMethod = config.enableMethod;
      this.disableMethod = config.disableMethod;
      this.keepOn = config.keepOn ?? true;
      this.enabled = config.enabled ?? false;
    }
  }

  let currentCategory = 0;
  let currentPage = 0;

  //#region Mods

  //#region Player
  let flyspeed = 5.0;
  let ghost = false;
  let spawnedRig = null;

  function Fly() {
    if (rightSecondary) {
      rigidbody.method("set_velocity").invoke(Vector3.field("zeroVector").value);

      const transform = getTransform(GorillaTagger);
      let forward = getTransform(rightHandTransform).method("get_forward").invoke();

      let position = transform.method("get_position").invoke();
      forward = Vector3.method("op_Multiply", 2).invoke(forward, flyspeed * deltaTime);

      position = Vector3.method("op_Addition", 2).invoke(position, forward);

      transform.method("set_position").invoke(position);
    }
  }

  //#region  Platforms
  let platColor: [number, number, number, number] = [0.0, 0.0, 0.0, 1.0];
  const platColors: [number, number, number, number][] = [
    [0.0, 0.0, 0.0, 1.0],       // Black
    [9.0, 9.0, 9.0, 1.0],       // Bright white
    [9.0, 0.0, 0.0, 1.0],       // Red
    [0.0, 9.0, 0.0, 1.0],       // Green
    [0.0, 0.0, 9.0, 1.0],       // Blue
    [5.0, 5.0, 0.0, 1.0],       // Yellow
    [9.0, 0.5, 9.0, 1.0],       // Magenta
  ];
  let platL: any = null;
  let platR: any = null;
  let plater = 0;

  function dumpServerInfo(): void {
    const PlayFabSettingsClass = Il2Cpp.domain.assembly("PlayFab").image.class("PlayFabSharedSettings");
    let settingsInstance: any = null;
    try {
      const instances = Il2Cpp.gc.choose(PlayFabSettingsClass);
      if (instances.length > 0) settingsInstance = instances[0];
    } catch (_) {}

    if (!settingsInstance) {
      try {
        console.log("[PlayFab] TitleId (via getter): " + PlayFabSettingsClass.method("get_TitleId").invoke());
      } catch (_) {}
    } else {
      console.log("[PlayFab] TitleId: " + settingsInstance.field("TitleId").value);
    }
  }

  function TPlatforms() {
    if (leftTrigger) {
      if (platL == null) {
        const handTransform = leftHandTransform;
        platL = createObject(Vector3.method("op_Addition", 2).invoke(handTransform.method("get_position").invoke(), [0.01, -0.035, 0.0]), handTransform.method("get_rotation").invoke(), [0.025, 0.25, 0.3], 3, platColor);
      }
    } else {
      if (platL != null) {
        Destroy(platL);
        platL = null;
      }
    }

    if (rightTrigger) {
      if (platR == null) {
        const handTransform = rightHandTransform;
        platR = createObject(Vector3.method("op_Addition", 2).invoke(handTransform.method("get_position").invoke(), [0.0, -0.035, 0.0]), handTransform.method("get_rotation").invoke(), [0.025, 0.25, 0.3], 3, platColor);
      }
    } else {
      if (platR != null) {
        Destroy(platR);
        platR = null;
      }
    }
  }

  function Platforms() {
    if (leftGrab) {
      if (platL == null) {
        const handTransform = leftHandTransform;
        platL = createObject(Vector3.method("op_Addition", 2).invoke(handTransform.method("get_position").invoke(), [0.01, -0.035, 0.0]), handTransform.method("get_rotation").invoke(), [0.025, 0.25, 0.3], 3, platColor);
      }
    } else {
      if (platL != null) {
        Destroy(platL);
        platL = null;
      }
    }

    if (rightTrigger) {
      if (platR == null) {
        const handTransform = rightHandTransform;
        platR = createObject(Vector3.method("op_Addition", 2).invoke(handTransform.method("get_position").invoke(), [0.0, -0.035, 0.0]), handTransform.method("get_rotation").invoke(), [0.025, 0.25, 0.3], 3, platColor);
      }
    } else {
      if (platR != null) {
        Destroy(platR);
        platR = null;
      }
    }
  }

  //#endregion

  //#region  NoClip

  function Noclip() {
    if (rightTrigger && !previousNoclipKey) {
      toggleColliders(false);
    }

    if (!rightTrigger && previousNoclipKey) {
      toggleColliders(true);
    }

    previousNoclipKey = rightTrigger;
  }

  function toggleColliders(enabled: any) {
    const meshColliders = Object.method("FindObjectsOfType").inflate(MeshCollider).invoke();

    for (let i = 0; i < meshColliders.length; i++) {
      const meshCollider = meshColliders.get(i);
      meshCollider.method("set_enabled").invoke(enabled);
    }
  }

  //#endregion

  //#endregion

  //#region Misc

  //#endregion

  //#region OP

function EnableStaffShit() {
  const objectsToEnable = [
    "KickButtons",
    "KickButton",
    "owner",
    "BanButtons",
    "BanButton",
    "Staff",
    "BanHammer",
    "Mod",
    "Modpower",
    "BanHammer",
    "KickHammer"
  ];
  for (let i = 0; i < objectsToEnable.length; i++) {
    try {
      const obj = GameObject.method("Find").invoke(Il2Cpp.string(objectsToEnable[i]));
      if (obj == null || (obj.isNull && obj.isNull()) || (obj.handle && obj.handle.isNull && obj.handle.isNull())) continue;
      obj.method("SetActive").invoke(true);
    } catch (_) {}
  }
}

  function OpenStaff() {
    const AllBoxColliders = Object.method("FindObjectsOfType").inflate(BoxCollider).invoke();
    for (let i = 0; i < AllBoxColliders.length; i++) {
      const Colid = AllBoxColliders.get(i);
      if (Colid.method("get_name").invoke().toString().includes("Cube")) {
        Colid.method("set_enabled").invoke(false);
      }
    }

    const objectsToDestroy = [
      "miroorcolideryeee",
      "Mod",
      "miroor colider",
      "hahahahahhahahhaheheheh",
      "AFJHDSUFHSDIUHHDSIUFHSIDOOR",
      "thingcol",
      "Cube (5)", "Plane", "Cube (9)", "Plane (1)", "Cube (3)", "Cube (4)", "Cube (6)",
      "Plane (2)", "Plane (3)", "Cube (7)", "Plane (5)", "Cube (12)", "Plane (4)", "Cube (10)",
      "Plane (6)", "Plane (7)", "Plane (9)", "Plane (8)", "Plane (10)", "Cube (11)", "Plane (11)",
      "Plane (9)",
      "Cube (8)", "Plane (12)", "Plane (13)", "Plane (14)", "Plane (15)", "Plane (16)",
      "Plane (17)", "Plane (18)", "Plane (19)", "Plane (20)", "Cube (13)"
    ];

    for (let i = 0; i < objectsToDestroy.length; i++) {
      Destroy(GameObject.method("Find").invoke(Il2Cpp.string(objectsToDestroy[i])));
    }
  }

  //#endregion

  //#endregion


  // Populates itemIDs (names) and itemPrefabHandles (prefab GameObject ptrs),
  // index-aligned, so itemIndex drives both cycling and spawning.
  function ensurePrefabList(): boolean {
    if (prefabListReady) return true;
    const names: string[] = [];
    const handles: any[] = [];

    // Source A: PrefabGenerator._itemPrefabDictionary - keys + GameObject values.
    try {
      const PGC = Il2Cpp.domain.assembly("AnimalCompany").image.class("AnimalCompany.PrefabGenerator");
      try { PGC.method(".cctor").invoke(); } catch (e: any) { console.log("PG cctor:", String(e)); }
      const d = PGC.field("_itemPrefabDictionary").value;
      if (!d || d.isNull?.()) console.log("_itemPrefabDictionary is null");
      else {
        const count = d.method("get_Count").invoke();
        console.log("_itemPrefabDictionary count:", count);
        if (count > 0) {
          const goClass = Il2Cpp.domain.assembly("UnityEngine.CoreModule").image.class("UnityEngine.GameObject");
          const strArr = Il2Cpp.array(Il2Cpp.corlib.class("System.String"), count);
          const goArr = Il2Cpp.array(goClass, count);
          d.method("get_Keys").invoke().method("CopyTo", 2).invoke(strArr, 0);
          d.method("get_Values").invoke().method("CopyTo", 2).invoke(goArr, 0);
          for (let i = 0; i < count; i++) {
            try {
              const k = strArr.get(i);
              const g = goArr.get(i);
              if (k && !k.isNull?.() && g && !g.isNull?.()) {
                names.push(String(k));
                handles.push(g.handle);
              }
            } catch (_) {}
          }
        }
      }
    } catch (e: any) { console.log("dictionary path failed:", String(e)); }

    // Source B: Fusion config sources. Resolve each into its prefab GameObject:
    // static sources expose Object directly; resource sources via
    // Acquire(true) -> WaitForResult() -> NetworkObject.gameObject.
    if (names.length === 0) {
      const FusionRuntime = Il2Cpp.domain.assembly("Fusion.Runtime").image;
      let sources = [];

      try {
        const asset = FusionRuntime.class("Fusion.NetworkProjectConfigAsset").method("get_Global").invoke();
        if (asset && !asset.isNull?.()) {
          const list = asset.field("Prefabs").value;
          if (list && !list.isNull?.()) {
            const count = list.method("get_Count").invoke();
            for (let i = 0; i < count; i++) sources.push(list.method("get_Item", 1).invoke(i));
          }
        }
      } catch (_) {}

      if (sources.length === 0) {
        try {
          const config = FusionRuntime.class("Fusion.NetworkProjectConfig").method("get_Global").invoke();
          if (config && !config.isNull?.()) {
            const table = config.field("PrefabTable").value;
            if (table && !table.isNull?.()) {
              const prefabs = table.method("get_Prefabs").invoke();
              const count = prefabs.method("get_Count").invoke();
              for (let i = 0; i < count; i++) sources.push(prefabs.method("get_Item", 1).invoke(i));
            }
          }
        } catch (_) {}
      }

      if (sources.length === 0) { console.log("no prefab sources found"); return false; }

      for (const src of sources) {
        let name = null;
        try { const rp = src.field("ResourcePath").value; if (rp && !rp.isNull?.()) name = rp.toString(); } catch (_) {}
        if (!name) { try { const ds = src.method("get_Description").invoke(); if (ds && !ds.isNull?.()) name = ds.toString(); } catch (_) {} }
        if (!name) {
          try {
            const obj = src.method("get_Prefab").invoke();
            if (obj && !obj.isNull?.()) {
              const n = obj.method("get_name").invoke();
              if (n && !n.isNull?.()) name = n.toString();
            }
          } catch (_) {}
        }
        let handle = null;
        try {
          const o = src.field("Object").value;
          if (o && !o.isNull?.()) handle = o.method("get_gameObject").invoke().handle;
        } catch (_) {}
        if (!handle) {
          try {
            src.method("Acquire", 1).invoke(true);
            const no = src.method("WaitForResult").invoke();
            if (no && !no.isNull?.()) handle = no.method("get_gameObject").invoke().handle;
          } catch (_) {}
        }
        names.push(name ? String(name) : "<unnamed>");
        handles.push(handle);
      }
    }

    const okCount = handles.filter((h: any) => !!h).length;
    console.log("prefab list built:", names.length, "entries,", okCount, "with usable prefab GameObjects");
    if (names.length > 0 && okCount > 0) {
      itemIDs = names;
      itemPrefabHandles = handles;
      prefabListReady = true;
      console.log("sample:", names.slice(0, Math.min(6, names.length)).join(", "));
      return true;
    }
    return false;
  }

  // Fuzzy-matches a short item name ("ColaCan", "Flashlight") against the
  // runtime prefab list and returns its spawn index.
  function findPrefabIndex(nm: string): number {
    ensurePrefabList();
    if (!nm || itemIDs.length === 0) return -1;
    const lower = nm.toLowerCase();
    let idx = itemIDs.findIndex((p) => p.toLowerCase() == lower);
    if (idx >= 0) return idx;
    idx = itemIDs.findIndex((p) => {
      const base = p.toLowerCase().split("/").pop() ?? "";
      return base == lower || base.startsWith(lower);
    });
    if (idx >= 0) return idx;
    return itemIDs.findIndex((p) => p.toLowerCase().includes(lower));
  }

  // Spawns an explicit prefab GameObject at `hitPoint`, mirroring the proven
  // egg-test mechanism (live prefab -> networked Vector3/Quaternion spawn):
  //   A) runner.Spawn(GameObject, ...)
  //   B) PrefabGenerator.SpawnItem with stripped basename
  //   C) guaranteed fallback: ChickenController.SpawnEgg at the hit point.
  function spawnPrefabHandle(handle: any, displayName: string, hitPoint: any): any {
    const px = hitPoint.field("x").value;
    const py = hitPoint.field("y").value + 0.1;
    const pz = hitPoint.field("z").value;
    const rx = identityQuaternion.field("x").value;
    const ry = identityQuaternion.field("y").value;
    const rz = identityQuaternion.field("z").value;
    const rw = identityQuaternion.field("w").value;

    // --- A) runner.Spawn(GameObject, ...) ---
    try {
      if (handle) {
        const AssemblyCSharp = Il2Cpp.domain.assembly("AnimalCompany").image;
        const PGClass = AssemblyCSharp.class("AnimalCompany.PrefabGenerator");
        const pg = PGClass.field("_instance").value;
        if (pg && !pg.isNull?.()) {
          const runner = pg.method("get_runner").invoke();
          if (runner && !runner.isNull?.()) {
            let spawnMethod: any = null;
            for (const m of runner.class.methods) {
              if (m.name != "Spawn" || m.isStatic) continue;
              const ps = m.parameters;
              if (!ps || ps.length != 6) continue;
              if (ps[0].type && ps[0].type.name == "UnityEngine.GameObject") { spawnMethod = m; break; }
            }
            if (spawnMethod) {
              if (!spawnDelegate) {
                const RunnerKlass = Il2Cpp.domain.assembly("Fusion.Runtime").image.class("Fusion.NetworkRunner");
                const ObSClass = RunnerKlass.nestedClasses.find((c: any) => c.name == "OnBeforeSpawned");
                spawnDelegate = Il2Cpp.delegate(ObSClass, (_runner: any, _obj: any) => {});
              }
              // Nullable<Vector3> = [hasValue,[x,y,z]], Nullable<Quaternion>
              // likewise, Nullable<PlayerRef> = [hasValue,[rawIndex]],
              // NetworkSpawnFlags = 0.
              const ptrA = spawnMethod.nativeFunction(
                runner.handle,
                handle,
                [1, [px, py, pz]],
                [1, [rx, ry, rz, rw]],
                [0, [0]],
                spawnDelegate.handle,
                0
              );
              if (ptrA && !ptrA.isNull()) {
                return new (Il2Cpp as any).Object(ptrA);
              }
            }
          }
        }
      }
    } catch (_) {}

    // --- B) SpawnItem with stripped basename ---
    try {
      let id = String(displayName);
      const slash = id.lastIndexOf("/");
      if (slash >= 0) id = id.substring(slash + 1);
      if (id.endsWith(".prefab")) id = id.substring(0, id.length - 7);
      const AssemblyCSharp2 = Il2Cpp.domain.assembly("AnimalCompany").image;
      const PGClass2 = AssemblyCSharp2.class("AnimalCompany.PrefabGenerator");
      let spawnItemMethod: any = null;
      for (const m of PGClass2.methods) {
        if (m.name == "SpawnItem" && m.isStatic && m.parameters.length == 5) { spawnItemMethod = m; break; }
      }
      if (!spawnDelegate) {
        const RunnerKlass2 = Il2Cpp.domain.assembly("Fusion.Runtime").image.class("Fusion.NetworkRunner");
        const ObSClass2 = RunnerKlass2.nestedClasses.find((c: any) => c.name == "OnBeforeSpawned");
        spawnDelegate = Il2Cpp.delegate(ObSClass2, (_runner: any, _obj: any) => {});
      }
      if (spawnItemMethod) {
        const ptrB = spawnItemMethod.nativeFunction(
          Il2Cpp.string(id),
          [px, py, pz],
          [rx, ry, rz, rw],
          1,
          spawnDelegate.handle
        );
        if (ptrB && !ptrB.isNull()) {
          return new (Il2Cpp as any).Object(ptrB);
        }
      }
    } catch (_) {}

    // --- C) egg fallback ---
    try {
      const CoreMod = Il2Cpp.domain.assembly("UnityEngine.CoreModule").image;
      const UObject = CoreMod.class("UnityEngine.Object");
      const chickenClass = Il2Cpp.domain.assembly("AnimalCompany").image.class("AnimalCompany.ChickenController");
      const found = UObject.method("FindObjectsOfType", 2).invoke(chickenClass.type.object.handle, 0);
      const chicks: any[] = Array.from(found as any);
      for (const chick of chicks) {
        try {
          if (chick.field("_eggPrefab").value && !chick.field("_eggPrefab").value.isNull?.()) {
            chick.method("SpawnEgg").invoke([px, py, pz], [rx, ry, rz, rw]);
            return chick;
          }
        } catch (_) {}
      }
    } catch (_) {}

    return null;
  }

  // Legacy entry: spawns whatever the item index currently points at.
  function spawnCurrentItem(hitPoint: any): any {
    ensurePrefabList();
    if (itemIDs.length === 0) { return null; }
    const handle = itemIndex < itemPrefabHandles.length ? itemPrefabHandles[itemIndex] : null;
    return spawnPrefabHandle(handle, String(itemIDs[itemIndex]), hitPoint);
  }

  // Guaranteed-working egg spawner: exact code path as the validated egg test
  // (live chicken's _eggPrefab through its own SpawnEgg method).
  function spawnEggAt(hitPoint: any): boolean {
    try {
      const CoreMod = Il2Cpp.domain.assembly("UnityEngine.CoreModule").image;
      const UObject = CoreMod.class("UnityEngine.Object");
      const chickenClass = Il2Cpp.domain.assembly("AnimalCompany").image.class("AnimalCompany.ChickenController");
      const found = UObject.method("FindObjectsOfType", 2).invoke(chickenClass.type.object.handle, 0);
      const chicks: any[] = Array.from(found as any);
      console.log("chickens found:", chicks.length);
      if (chicks.length <= 0) return false;
      for (const chick of chicks) {
        try {
          const eggPrefab = chick.field("_eggPrefab").value;
          if (eggPrefab && !eggPrefab.isNull?.()) {
            const px = hitPoint.field("x").value;
            const py = hitPoint.field("y").value + 0.1;
            const pz = hitPoint.field("z").value;
            const rx = identityQuaternion.field("x").value;
            const ry = identityQuaternion.field("y").value;
            const rz = identityQuaternion.field("z").value;
            const rw = identityQuaternion.field("w").value;
            chick.method("SpawnEgg").invoke([px, py, pz], [rx, ry, rz, rw]);
            console.log("SpawnEgg called at", px, py, pz);
            return true;
          }
        } catch (_) {}
      }
      return false;
    } catch (e) {
      console.error("spawnEggAt error:", String(e));
      return false;
    }
  }

  // GameManager-backed collectible item list (enables the static item constants).
  const TELE_ITEM_FIELDS = [
    ["ITEM_NAME_COLACAN", "COST_COLACAN"],
    ["ITEM_NAME_COLACAN_LARGE", "COST_COLACAN_LARGE"],
    ["ITEM_NAME_BANANA", "COST_BANANA"],
    ["ITEM_NAME_BANANA_LARGE", "COST_BANANA_LARGE"],
    ["ITEM_NAME_FLASHLIGHT", "COST_FLASHLIGHT"],
    ["ITEM_NAME_EGG", "COST_EGG"]
  ];
  let teleItemCache: { name: string; pid: number; cost: number }[] | null = null;

  function resolveGameManagerItems(): { name: string; pid: number; cost: number }[] {
    if (teleItemCache && teleItemCache.length) return teleItemCache;
    const out: { name: string; pid: number; cost: number }[] = [];
    try {
      const GMClass = AssemblyCSharp.class("AnimalCompany.GameManager");
      for (const [nameField, costField] of TELE_ITEM_FIELDS) {
        let nm = "";
        try { nm = GMClass.field(nameField).value.toString(); } catch (_) {}
        if (!nm) continue;
        let pid = findPrefabIndex(nm);
        let cost = 0;
        try { cost = GMClass.field(costField).value; } catch (_) {}
        out.push({ name: nm, pid: pid >= 0 ? pid : 0, cost });
      }
    } catch (e) {
      console.log("GameManager items read error:", String(e));
    }
    // Fallback to fuzzy-matching known item names against the runtime prefab list.
    if (out.length === 0) {
      const fallback = ["ColaCan", "ColaCan_Large", "Banana", "Banana_Large", "Flashlight", "Egg"];
      for (const nm of fallback) {
        const pid = findPrefabIndex(nm);
        out.push({ name: nm, pid: pid >= 0 ? pid : 0, cost: 0 });
      }
    }
    teleItemCache = out;
    return out;
  }

  function getGameManagerItemNames(): string[] {
    return resolveGameManagerItems().map((i) => i.name);
  }

  function getGameManagerItemPids(): number[] {
    return resolveGameManagerItems().map((i) => i.pid);
  }

  const buttons: ButtonInfo[][] = [

    [ // Home
      new ButtonInfo({
        buttonText: "Settings",
        method: () => currentCategory = 2,
        keepOn: false,
      }),
      new ButtonInfo({
        buttonText: "Movement Mods",
        method: () => currentCategory = 3,
        keepOn: false,
      }),
      new ButtonInfo({
        buttonText: "Misc Mods",
        method: () => currentCategory = 4,
        keepOn: false,
      }),
      new ButtonInfo({
        buttonText: "Rig Mods",
        method: () => currentCategory = 5,
        keepOn: false,
      }),
      new ButtonInfo({
        buttonText: "Name Mods",
        method: () => { currentCategory = 6 },
        keepOn: false,
      }),
      new ButtonInfo({
        buttonText: "OP Mods",
        method: () => currentCategory = 7,
        keepOn: false,
      }),
      new ButtonInfo({
        buttonText: "Prefab Mods",
        method: () => { currentCategory = 8 },
        keepOn: false,
      }),
    ],

    [ // Menu Buttons
      new ButtonInfo({
        buttonText: "Leave",
        method: () => console.log(""),
        keepOn: false,
      }),

      new ButtonInfo({
        buttonText: "Home",
        method: () => {
          currentCategory = 0
          currentPage = 0
        },
        keepOn: false,
      }),
      new ButtonInfo({
        buttonText: "PreviousPage",
        method: () => {
          const lastPage = Math.ceil(buttons[currentCategory].length / 6) - 1;

          currentPage--;
          if (currentPage < 0)
            currentPage = lastPage;
        },
        keepOn: false
      }),
      new ButtonInfo({
        buttonText: "NextPage",
        method: () => {
          const lastPage = Math.ceil(buttons[currentCategory].length / 6) - 1;

          currentPage++;
          currentPage %= lastPage + 1;
        },
        keepOn: false
      })
    ],

    [ // Settings
      new ButtonInfo({
        buttonText: `Fly Speed+`,
        method: () => {
          flyspeed += 1
          reloadMenu();
        },
        keepOn: false,
      }),

      new ButtonInfo({
        buttonText: `Fly Speed-`,
        method: () => {
          flyspeed -= 1
          reloadMenu();
        },
        keepOn: false,
      }),

      new ButtonInfo({
        buttonText: "Platform Color",
        method: () => {
          plater = (plater + 1) % platColors.length;
          platColor = platColors[plater];
        },
        keepOn: false,
      }),
    ],

    [ // Movement Mods
      new ButtonInfo({
        buttonText: "Fly [B]",
        method: () => {
          Fly()
        },
      }),

      new ButtonInfo({
        buttonText: "Trigger Platforms [T]",
        method: () => {
          TPlatforms()
        },
      }),

      new ButtonInfo({
        buttonText: "Platforms [G]",
        method: () => {
          Platforms()
        },
      }),

      new ButtonInfo({
        buttonText: "Long Arms",
        method: () => {
            getTransform(GorillaTagger).method("set_localScale").invoke([1.25, 1.25, 1.25]);
        },
        keepOn: false,
      }),

      new ButtonInfo({
        buttonText: "Longer Arms",
        method: () => {
            getTransform(GorillaTagger).method("set_localScale").invoke([1.3, 1.3, 1.3]);
        },
        keepOn: false,
      }),

      new ButtonInfo({
        buttonText: "Fix Arms",
        method: () => {
            getTransform(GorillaTagger).method("set_localScale").invoke([1.0, 1.0, 1.0]);
        },
        keepOn: false,
      }),

      new ButtonInfo({
        buttonText: "Toggle Gravity",
        method: () => {
          const current = rigidbody.method("get_useGravity").invoke() as boolean;
          rigidbody.method("set_useGravity").invoke(!current);
        },
        keepOn: false
      }),
    ],

    [ // Misc Mods

    ],

    [ // Rig Mods

    ],

    [ // Name Mods
new ButtonInfo({
  buttonText: "J0kerClient",
  method: () => {
    try {
      const NetPlayer = Il2Cpp.domain.assembly("AnimalCompany").image.class("AnimalCompany.NetPlayer");

      const local = NetPlayer.method("get_localPlayer").invoke();
      if (!local || local.isNull?.()) {
        console.log("Local player not found");
        return;
      }

      local.method("set_displayName").invoke(Il2Cpp.string("J0kerClient"));
      console.log("Name set");
    } catch (e) {
      console.log("Set My Name error:", e);
    }
  },
  keepOn: false,
}),
    ],

    [ // OP Mods
new ButtonInfo({
  buttonText: "Godmode",
  method: () => {
    try {
      const PlayerController = Il2Cpp.domain
        .assembly("AnimalCompany")
        .image.class("AnimalCompany.PlayerController");
      const NetPlayer = Il2Cpp.domain
        .assembly("AnimalCompany")
        .image.class("AnimalCompany.NetPlayer");

      let pc = PlayerController.field("_instance").value;
      if (!pc || pc.isNull?.()) {
        pc = Object.method("FindObjectOfType").inflate(PlayerController).invoke();
      }
      if (pc && !pc.isNull?.()) {
        try { pc.method("SetCurrentHealth").invoke(9999999999); } catch (e) {
          pc.field("_currHealth").value = 999999999999;
        }
        try { pc.field("_isDie").value = false; } catch (e) {}
      }

      const local = NetPlayer.method("get_localPlayer").invoke();
      if (local && !local.isNull?.()) {
        try {
          local.method("set_isDie").invoke(false);
          local.method("RPC_DoPlayerDie").invoke(false);
          local.method("RPC_PlayerHit").invoke(0);
        } catch (e) {}
      }
    } catch (e) {
      console.log("Godmode error:", e);
    }
  },
  keepOn: true,
}),

new ButtonInfo({
  buttonText: "Hit Gun [G]",
  method: () => {
    if (!rightTrigger) return;
    try {
      const gunData = renderGun();
      const gunPointer = gunData.gunPointer;
      if (!gunPointer) return;

      const NetPlayer = Il2Cpp.domain.assembly("AnimalCompany").image.class("AnimalCompany.NetPlayer");
      const Vector3 = Il2Cpp.domain.assembly("UnityEngine.CoreModule").image.class("UnityEngine.Vector3");

      const players = NetPlayer.method("get_spawnedPlayers").invoke();
      if (!players || players.isNull?.()) return;

      const pointerPos = getTransform(gunPointer).method("get_position").invoke();

      const values = players.method("get_Values").invoke();
      const iter = values.method("GetEnumerator").invoke();
      let closest = null;
      let closestDist = 999;

      while (iter.method("MoveNext").invoke()) {
        const p = iter.method("get_Current").invoke();
        if (!p || p.isNull?.() || p.method("get_IsMine").invoke()) continue;
        try {
          const head = p.field("head").value;
          if (!head || head.isNull?.()) continue;
          const hp = head.method("get_position").invoke();
          const dx = hp.field("x").value - pointerPos.field("x").value;
          const dy = hp.field("y").value - pointerPos.field("y").value;
          const dz = hp.field("z").value - pointerPos.field("z").value;
          const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
          if (dist < closestDist && dist < 10) {
            closestDist = dist;
            closest = p;
          }
        } catch (e) {}
      }

      if (closest) {
        const head = closest.field("head").value;
        const pos = head.method("get_position").invoke();
        const rot = head.method("get_rotation").invoke();

        // Zero vector (required by RPC, no knockback)
        const zero = Vector3.alloc();
        zero.field("x").value = 0;
        zero.field("y").value = 0;
        zero.field("z").value = 0;
        const zeroForce = new Il2Cpp.ValueType(zero.handle, Vector3.type);

        closest.method("RPC_PlayerHit").overload(
          "System.Int32",
          "UnityEngine.Vector3",
          "UnityEngine.Quaternion",
          "System.String",
          "System.String",
          "UnityEngine.Vector3"
        ).invoke(
          50,
          pos,
          rot,
          Il2Cpp.string(""),
          Il2Cpp.string(""),
          zeroForce
        );
      }
    } catch (e) {
      console.log("Hit Gun error:", e);
    }
  },
  keepOn: true,
}),
new ButtonInfo({
  buttonText: "Void Gun [G]",
  method: () => {
    if (!rightTrigger) return;

    try {
      const gunData = renderGun();
      const gunPointer = gunData.gunPointer;
      if (!gunPointer) return;

      const NetPlayer = Il2Cpp.domain.assembly("AnimalCompany").image.class("AnimalCompany.NetPlayer");
      const Vector3 = Il2Cpp.domain.assembly("UnityEngine.CoreModule").image.class("UnityEngine.Vector3");
      const Quaternion = Il2Cpp.domain.assembly("UnityEngine.CoreModule").image.class("UnityEngine.Quaternion");

      const players = NetPlayer.method("get_spawnedPlayers").invoke();
      if (!players || players.isNull?.()) return;

      const pointerPos = getTransform(gunPointer).method("get_position").invoke();
      const forward = getTransform(gunPointer).method("get_forward").invoke();

      function makeVec3(x: any, y: any, z: any) {
        const v = Vector3.alloc();
        v.field("x").value = x;
        v.field("y").value = y;
        v.field("z").value = z;
        return new Il2Cpp.ValueType(v.handle, Vector3.type);
      }

      const forcePower = 0;
      const force = makeVec3(
        forward.field("x").value * forcePower,
        forward.field("y").value * forcePower,
        forward.field("z").value * forcePower
      );

      const values = players.method("get_Values").invoke();
      const iter = values.method("GetEnumerator").invoke();

      let closest = null;
      let closestDist = 999;

      while (iter.method("MoveNext").invoke()) {
        const p = iter.method("get_Current").invoke();
        if (!p || p.isNull?.() || p.method("get_IsMine").invoke()) continue;

        try {
          const head = p.field("head").value;
          if (!head || head.isNull?.()) continue;

          const hp = head.method("get_position").invoke();
          const dx = hp.field("x").value - pointerPos.field("x").value;
          const dy = hp.field("y").value - pointerPos.field("y").value;
          const dz = hp.field("z").value - pointerPos.field("z").value;
          const dist = Math.sqrt(dx*dx + dy*dy + dz*dz);

          if (dist < closestDist && dist < 10) {
            closestDist = dist;
            closest = p;
          }
        } catch (e) {}
      }

      if (closest) {
        const head = closest.field("head").value;
        const pos = head.method("get_position").invoke();
        const rot = head.method("get_rotation").invoke();

        // RPC_PlayerHit(damage, pos, rot, hitSound, killSound, force)
        closest.method("RPC_PlayerHit").overload(
          "System.Int32",
          "UnityEngine.Vector3",
          "UnityEngine.Quaternion",
          "System.String",
          "System.String",
          "UnityEngine.Vector3"
        ).invoke(
          50,
          pos,
          rot,
          Il2Cpp.string(""),
          Il2Cpp.string(""),
          force
        );
      }
    } catch (e) {
      console.log("Hit Gun error:", e);
    }
  },
  keepOn: true,
}),
new ButtonInfo({
  buttonText: "Kill All",
  method: () => {
    try {
      const NetPlayer = Il2Cpp.domain.assembly("AnimalCompany").image.class("AnimalCompany.NetPlayer");
      const Vector3 = Il2Cpp.domain.assembly("UnityEngine.CoreModule").image.class("UnityEngine.Vector3");
      const Quaternion = Il2Cpp.domain.assembly("UnityEngine.CoreModule").image.class("UnityEngine.Quaternion");

      const players = NetPlayer.method("get_spawnedPlayers").invoke();
      if (!players || players.isNull?.()) return;

      function makeVec3(x: any, y: any, z: any) {
        const v = Vector3.alloc();
        v.field("x").value = x;
        v.field("y").value = y;
        v.field("z").value = z;
        return new Il2Cpp.ValueType(v.handle, Vector3.type);
      }

      function makeQuat(x: any, y: any, z: any, w: any) {
        const q = Quaternion.alloc();
        q.field("x").value = x;
        q.field("y").value = y;
        q.field("z").value = z;
        q.field("w").value = w;
        return new Il2Cpp.ValueType(q.handle, Quaternion.type);
      }

      const zeroPos = makeVec3(0, 0, 0);
      const identityRot = makeQuat(0, 0, 0, 1);
      const zeroForce = makeVec3(0, 0, 0);

      const values = players.method("get_Values").invoke();
      const iter = values.method("GetEnumerator").invoke();

      while (iter.method("MoveNext").invoke()) {
        const p = iter.method("get_Current").invoke();
        if (!p || p.isNull?.()) continue;
        if (p.method("get_IsMine").invoke()) continue;

        try {
          let pos = zeroPos;
          let rot = identityRot;

          try {
            const head = p.field("head").value;
            if (head && !head.isNull?.()) {
              pos = head.method("get_position").invoke();
              rot = head.method("get_rotation").invoke();
            }
          } catch (e) {}

          // RPC_PlayerHit(damage, position, rotation, hitSound, killSound, force)
          p.method("RPC_PlayerHit").overload(
            "System.Int32",
            "UnityEngine.Vector3",
            "UnityEngine.Quaternion",
            "System.String",
            "System.String",
            "UnityEngine.Vector3"
          ).invoke(
            999999,
            pos,
            rot,
            Il2Cpp.string(""),
            Il2Cpp.string(""),
            zeroForce
          );
        } catch (e) {
          // fallback: simpler overload without force
          try {
            p.method("RPC_PlayerHit").overload(
              "System.Int32",
              "UnityEngine.Vector3",
              "UnityEngine.Quaternion",
              "System.String",
              "System.String"
            ).invoke(
              999999,
              zeroPos,
              identityRot,
              Il2Cpp.string(""),
              Il2Cpp.string("")
            );
          } catch (e2) {}
        }
      }
    } catch (e) {
      console.log("Kill All error:", e);
    }
  },
  keepOn: false,
}),

new ButtonInfo({
  buttonText: "Spam Reload",
  method: () => {
    try {
      const Shotgun = Il2Cpp.domain.assembly("AnimalCompany").image.class("AnimalCompany.Shotgun");
      const guns = Object.method("FindObjectsOfType").inflate(Shotgun).invoke();

      for (let i = 0; i < guns.length; i++) {
        const gun = guns.get ? guns.get(i) : guns[i];
        if (!gun || gun.isNull?.()) continue;

        try {
          gun.method("set__ammoLeft").invoke(2);
        } catch (e) {}
      }
    } catch (e) {
      console.log("Reload error:", e);
    }
  },
  keepOn: true,
}),
new ButtonInfo({
  buttonText: "Inf Ammo & No CD",
  method: () => {
    try {
      const AnimalCo = Il2Cpp.domain.assembly("AnimalCompany").image;
      const FusionRun = Il2Cpp.domain.assembly("Fusion.Runtime").image;
      let noneTimer: any = null;
      try {
        noneTimer = FusionRun.class("Fusion.TickTimer").method("get_None").invoke();
      } catch (e) {}

      const Shotgun = AnimalCo.class("AnimalCompany.Shotgun");
      const shotguns = Object.method("FindObjectsOfType").inflate(Shotgun).invoke();
      for (let i = 0; i < shotguns.length; i++) {
        const sg = shotguns.get ? shotguns.get(i) : shotguns[i];
        if (!sg || sg.isNull?.()) continue;
        try { sg.method("set__ammoLeft").invoke(255); } catch (e) {}
        try {
          const gunField = sg.field("_gun").value;
          if (gunField && !gunField.isNull?.() && noneTimer) {
            gunField.method("set_shootTimer").invoke(noneTimer);
          }
        } catch (e) {}
      }

      const Revolver = AnimalCo.class("AnimalCompany.Revolver");
      const revolvers = Object.method("FindObjectsOfType").inflate(Revolver).invoke();
      for (let i = 0; i < revolvers.length; i++) {
        const rv = revolvers.get ? revolvers.get(i) : revolvers[i];
        if (!rv || rv.isNull?.()) continue;
        try { rv.method("set_ammoLoaded").invoke(255); } catch (e) {}
        try { rv.method("set_isHammerCocked").invoke(true); } catch (e) {}
        try { rv.method("set_cylinderIndex").invoke(0); } catch (e) {}
        try {
          const gunField = rv.field("_gun").value;
          if (gunField && !gunField.isNull?.() && noneTimer) {
            gunField.method("set_shootTimer").invoke(noneTimer);
          }
        } catch (e) {}
      }
      try {
        infAmmoRevolverCock = true;
      } catch (e) {}

      const FlareGun = AnimalCo.class("AnimalCompany.FlareGun");
      const flareGuns = Object.method("FindObjectsOfType").inflate(FlareGun).invoke();
      for (let i = 0; i < flareGuns.length; i++) {
        const fg = flareGuns.get ? flareGuns.get(i) : flareGuns[i];
        if (!fg || fg.isNull?.()) continue;
        try { fg.method("set_hasAmmo").invoke(1); } catch (e) {}
      }

      const Gun = AnimalCo.class("AnimalCompany.Gun");
      const allGuns = Object.method("FindObjectsOfType").inflate(Gun).invoke();
      for (let i = 0; i < allGuns.length; i++) {
        const g = allGuns.get ? allGuns.get(i) : allGuns[i];
        if (!g || g.isNull?.()) continue;
        try { if (noneTimer) g.method("set_shootTimer").invoke(noneTimer); } catch (e) {}
        try {
          const cfg = g.field("_config").value;
          if (cfg && !cfg.isNull?.()) {
            try { cfg.field("shootTime").value = 0.0; } catch (e) {}
            try { cfg.field("maxAmmo").value = 255; } catch (e) {}
          }
        } catch (e) {}
      }
    } catch (e) {
      console.log("Inf Ammo & No CD error:", e);
    }
  },
  keepOn: false,
}),
new ButtonInfo({
  buttonText: "Unlock All Items",
  method: () => {
    try {
      const AnimalCo = Il2Cpp.domain.assembly("AnimalCompany").image;
      const AppClass = AnimalCo.class("AnimalCompany.App");
      const appState = AppClass.method("get_state").invoke();
      if (!appState || appState.isNull?.()) { console.log("Unlock All: AppState null"); return; }
      const userState = appState.method("get_user").invoke();
      if (!userState || userState.isNull?.()) { console.log("Unlock All: UserState null"); return; }
      const invState = userState.method("get_inventory").invoke();
      if (!invState || invState.isNull?.()) { console.log("Unlock All: UserInventoryState null"); return; }
      const unlocked = invState.method("get_unlockedGameplayItems").invoke();
      if (!unlocked || unlocked.isNull?.()) { console.log("Unlock All: unlockedGameplayItems null"); return; }

      ensurePrefabList();
      const AddMethod = unlocked.method("Add");
      const DelegateCmdClass = Il2Cpp.domain.assembly("SpatialSys.CommandLib").image.class("SpatialSys.CommandLib.DelegateCommand");
      const ActionClass = Il2Cpp.corlib.class("System.Action");
      const actionDelegate = Il2Cpp.delegate(ActionClass, () => {
        for (let i = 0; i < itemIDs.length; i++) {
          try {
            AddMethod.invoke(Il2Cpp.string(String(itemIDs[i])));
          } catch (_) {}
        }
      });
      const cmdObj = DelegateCmdClass.alloc();
      DelegateCmdClass.method(".ctor").invokeRaw(cmdObj, actionDelegate);
      AppClass.method("ExecuteCommand").invoke(cmdObj, false);
      console.log("Unlock All Items: dispatched", itemIDs.length, "items via DelegateCommand");
    } catch (e) {
      console.log("Unlock All Items error:", e);
    }
  },
  keepOn: false,
}),
new ButtonInfo({
  buttonText: "Unlock All Research",
  method: () => {
    try {
      const AnimalCo = Il2Cpp.domain.assembly("AnimalCompany").image;
      const AppClass = AnimalCo.class("AnimalCompany.App");
      const appState = AppClass.method("get_state").invoke();
      if (!appState || appState.isNull?.()) { console.log("Unlock Research: AppState null"); return; }
      const userState = appState.method("get_user").invoke();
      if (!userState || userState.isNull?.()) { console.log("Unlock Research: UserState null"); return; }
      const invState = userState.method("get_inventory").invoke();
      if (!invState || invState.isNull?.()) { console.log("Unlock Research: UserInventoryState null"); return; }
      const researchNodes = invState.method("get_researchNodes").invoke();
      if (!researchNodes || researchNodes.isNull?.()) { console.log("Unlock Research: researchNodes null"); return; }

      const researchAppState = appState.method("get_researchData").invoke();
      if (!researchAppState || researchAppState.isNull?.()) { console.log("Unlock Research: researchData null"); return; }
      const nodesDict = researchAppState.method("get_nodes").invoke();
      if (!nodesDict || nodesDict.isNull?.()) { console.log("Unlock Research: nodes dict null"); return; }

      const keysCollection = nodesDict.method("get_Keys").invoke();
      const EnumerableClass = Il2Cpp.domain.assembly("System.Core").image.class("System.Linq.Enumerable");
      const StringClass = Il2Cpp.corlib.class("System.String");
      const toArrayGeneric = EnumerableClass.method("ToArray").inflate(StringClass);
      const allKeys = toArrayGeneric.invoke(keysCollection);
      const keyCount = allKeys.length;

      const AddMethod = researchNodes.method("Add");
      const DelegateCmdClass = Il2Cpp.domain.assembly("SpatialSys.CommandLib").image.class("SpatialSys.CommandLib.DelegateCommand");
      const ActionClass = Il2Cpp.corlib.class("System.Action");
      const actionDelegate = Il2Cpp.delegate(ActionClass, () => {
        for (let i = 0; i < keyCount; i++) {
          try {
            AddMethod.invoke(allKeys.get(i));
          } catch (_) {}
        }
      });
      const cmdObj = DelegateCmdClass.alloc();
      DelegateCmdClass.method(".ctor").invokeRaw(cmdObj, actionDelegate);
      AppClass.method("ExecuteCommand").invoke(cmdObj, false);
      console.log("Unlock All Research: dispatched", keyCount, "nodes via DelegateCommand");
    } catch (e) {
      console.log("Unlock All Research error:", e);
    }
  },
  keepOn: false,
}),
new ButtonInfo({
  buttonText: "No Despawn",
  method: () => {
    try {
      const AnimalCo = Il2Cpp.domain.assembly("AnimalCompany").image;
      const GI = AnimalCo.class("AnimalCompany.GrabbableItem");
      GI.method("RespawnOrDespawn").implementation = function () {};
      GI.method("Despawn").implementation = function () {};
      const ADI = AnimalCo.class("AnimalCompany.AutoDestroyItem");
      ADI.method("FixedUpdateNetwork").implementation = function () {};
      console.log("No Despawn: GrabbableItem.RespawnOrDespawn + Despawn + AutoDestroyItem.FixedUpdateNetwork neutered");
    } catch (e) {
      console.log("No Despawn error:", e);
    }
  },
  keepOn: false,
}),
new ButtonInfo({
  buttonText: "Spam Flashlight RPC",
  method: () => {
    try {
      const Flashlight = Il2Cpp.domain.assembly("AnimalCompany").image.class("AnimalCompany.Flashlight");
      const lights = Object.method("FindObjectsOfType").inflate(Flashlight).invoke();

      if (!lights || lights.length === 0) {
        console.log("No flashlights found");
        return;
      }

      for (let i = 0; i < lights.length; i++) {
        const fl = lights.get ? lights.get(i) : lights[i];
        if (!fl || fl.isNull?.()) continue;

        try {
          fl.method("RPC_ToggleOnOff").invoke();
        } catch (e) {}
      }
    } catch (e) {
      console.log("Spam Flashlight error:", e);
    }
  },
  keepOn: true, // spams every frame while on
}),
new ButtonInfo({
  buttonText: "Spawn Shit [G]",
  method: () => {

    // Show/update the gun pointer while grip is held
    if (rightTrigger) {
      const gunData = renderGun();
      const gunPointer = gunData.gunPointer;

      if (!gunPointer) return;

      // Execute once when Trigger is pressed
      if (!rightTrigger) {
        try {
          const PrefabGenerator = Il2Cpp.domain
            .assembly("AnimalCompany")
            .image.class("AnimalCompany.PrefabGenerator");

          const pointerTransform = getTransform(gunPointer);

          const pos = pointerTransform.method("get_position").invoke();
          const rot = pointerTransform.method("get_rotation").invoke();

          // 0 = DeadBody_Poop, 1 = Splashes
          PrefabGenerator.method("GeneratePrefab").invoke(0, pos, rot, false);

          console.log("Prefab spawned at gun pointer");
        } catch (e) {
          console.log("Spawn error:", e);
        }
      }
    }
  },
  keepOn: true,
}),
new ButtonInfo({
  buttonText: "Item TP Gun [G]",
  method: () => {
    if (!rightTrigger || !rightTrigger) return;

    try {
      const gunData = renderGun();
      const gunPointer = gunData.gunPointer;
      if (!gunPointer) return;

      const GrabbableItem = Il2Cpp.domain.assembly("AnimalCompany").image.class("AnimalCompany.GrabbableItem");
      const targetPos = getTransform(gunPointer).method("get_position").invoke();

      const items = Object.method("FindObjectsOfType").inflate(GrabbableItem).invoke();

      for (let i = 0; i < items.length; i++) {
        const item = items.get ? items.get(i) : items[i];
        if (!item || item.isNull?.()) continue;

        try {
          item.method("RPC_Teleport").invoke(targetPos);
        } catch (e) {}
      }
    } catch (e) {
      console.log("Item TP Gun error:", e);
    }
  },
  keepOn: true,
}),
new ButtonInfo({
  buttonText: "Respawn All Items",
  method: () => {
    try {
      const GrabbableItem = Il2Cpp.domain.assembly("AnimalCompany").image.class("AnimalCompany.GrabbableItem");
      const items = Object.method("FindObjectsOfType").inflate(GrabbableItem).invoke();

      for (let i = 0; i < items.length; i++) {
        const item = items.get ? items.get(i) : items[i];
        if (!item || item.isNull?.()) continue;
        try {
          item.method("Respawn").invoke();
        } catch (e) {}
      }
    } catch (e) {
      console.log("Respawn Items error:", e);
    }
  },
  keepOn: false,
}),
new ButtonInfo({
    buttonText: "Rapid Fire",
    method: () => {
        try {
            const NetPlayerClass = Il2Cpp.domain
                .assembly("AnimalCompany")
                .image.class("AnimalCompany.NetPlayer");

            const player = NetPlayerClass
                .method("get_localPlayer")
                .invoke();

            if (!player || player.isNull?.()) {
                console.log("Rapid Fire: local player not found");
                return;
            }

            const interactors = player.field("_interactors").value;

            if (!interactors || interactors.isNull?.()) {
                console.log("Rapid Fire: interactors not found");
                return;
            }

            // 0 = one hand, 1 = the other hand.
            // Swap these if your game's ordering is reversed.
            const rightInteractor = interactors.get(1);
            const leftInteractor = interactors.get(0);

            if (rightTrigger && rightInteractor && !rightInteractor.isNull?.()) {
                const anchor = rightInteractor
                    .method("get_itemAnchor")
                    .invoke();

                if (anchor && !anchor.isNull?.()) {
                    const item = anchor
                        .method("get_grabbableItem")
                        .invoke();

                    if (item && !item.isNull?.()) {
                        item.method("HandleTriggerUse").invoke();
                    }
                }
            }

            if (leftTrigger && leftInteractor && !leftInteractor.isNull?.()) {
                const anchor = leftInteractor
                    .method("get_itemAnchor")
                    .invoke();

                if (anchor && !anchor.isNull?.()) {
                    const item = anchor
                        .method("get_grabbableItem")
                        .invoke();

                    if (item && !item.isNull?.()) {
                        item.method("HandleTriggerUse").invoke();
                    }
                }
            }
        }
        catch (e) {
            console.error("Rapid Fire error:", e);
        }
    },

    keepOn: true,
}),
            new ButtonInfo({
                buttonText: "TP ALL Gun",
                method: () => {
                    if (!rightTrigger)
                        return;
                    const gunData = renderGun();
                    const ray = gunData.ray;
                    if (!rightTrigger)
                        return;
                    if (!ray || ray.isNull())
                        return;
                    try {
                        const hitPoint = ray.method("get_point").invoke();
                        const playerDict = NetPlayer.field("TryGetPlayerByID").value;
                        const playerValues = playerDict.method("get_Values").invoke();
                        const enumerator = playerValues.method("GetEnumerator").invoke();
                        while (enumerator.method("MoveNext").invoke()) {
                            const netPlayer = enumerator.method("get_Current").invoke();
                            if (!netPlayer || netPlayer.handle.isNull())
                                continue;
                            if (netPlayer.method("get_IsMine").invoke())
                                continue;
                            netPlayer.method("RPC_Teleport").invoke(hitPoint);
                        }
                    }
                    catch (e) {
                        console.error("TP ALL Gun error:", e);
                    }
                },
    keepOn: true,
            }),
new ButtonInfo({
  buttonText: "Inf Money",
  method: () => {
    try {
      // Money is stored on GameManager._scoreText (TMPro) in this build; DataStoreManager is gone.
      const GMClass = AssemblyCSharp.class("AnimalCompany.GameManager");
      let inst = null;
      try { inst = GMClass.method("get_instance").invoke(); } catch (_) {}
      if (!inst || inst.isNull?.()) {
        inst = GMClass.field("_instance").value;
      }
      if (!inst || inst.isNull?.()) { console.log("Inf Money: GameManager._instance null (load a map first)"); return; }
      const scoreText = inst.field("_scoreText").value;
      if (!scoreText || scoreText.isNull?.()) { console.log("Inf Money: _scoreText is null"); return; }
      // Try the TMP_Text.set_text(string) overload; fall back to the m_text backing field.
      let set = null;
      try { set = scoreText.method("set_text", 1); } catch (_) {}
      if (set) {
        set.invoke(Il2Cpp.string("999999999"));
        console.log("Money set to 999999999 via _scoreText");
      } else {
        try { scoreText.field("m_text").value = Il2Cpp.string("999999999"); console.log("Money set to 999999999 via m_text"); }
        catch (e2) { console.log("Inf Money: cannot set score text:", String(e2)); }
      }
    } catch (e) {
      console.log("Inf Money error:", String(e));
    }
  },
  keepOn: true,
}),
    ],
    [ // Prefabs - one gun button per loaded prefab
...(() => {
  const section: ButtonInfo[] = [];
  try {
    ensurePrefabList();
    const seen = new Set<string>();
    for (let i = 0; i < itemPrefabHandles.length; i++) {
      let nm = String(itemIDs[i]);
      const slash = nm.lastIndexOf("/");
      if (slash >= 0) nm = nm.substring(slash + 1);
      if (nm.endsWith(".prefab")) nm = nm.substring(0, nm.length - 7);
      if (!nm) nm = "prefab_" + i;
      while (seen.has(nm)) nm = nm + "_" + i;
      seen.add(nm);
      const idx = i;
      const label = nm;
      section.push(new ButtonInfo({
        buttonText: label + " gun",
        method: () => {
          if (!rightTrigger)
            return;
          let gunData: any = null;
          try {
            gunData = renderGun();
          } catch (e) {
            return;
          }
          const ray = gunData.ray;
          if (!ray || ray.handle.isNull())
            return;
          if (rightTrigger && time > tagGunDelay) {
            tagGunDelay = time + 0.1;
            try {
              const hitPoint = ray.method("get_point").invoke();
              spawnPrefabHandle(itemPrefabHandles[idx], label, hitPoint);
            }
            catch (e) {
              console.error(label + " gun error:", String(e));
            }
          }
        },
        keepOn: true,
      }));
    }
    console.log("prefab gun buttons generated:", section.length);
  } catch (e) {
    console.error("prefab gun generation failed:", String(e));
    section.push(new ButtonInfo({
      buttonText: "(prefab list failed to load)",
      method: () => { console.log("prefab list failed at menu init; check logs"); },
      keepOn: false,
    }));
  }
  return section;
})(),
new ButtonInfo({
  buttonText: "Dump Prefab Names",
  method: () => {
    try {
      console.log("=== Dump Prefab Names ===");

      const FusionRuntime = Il2Cpp.domain.assembly("Fusion.Runtime").image;
      let sources = [];

      // Path 1: NetworkProjectConfigAsset (ScriptableObject global) -> Prefabs list
      try {
        const assetClass = FusionRuntime.class("Fusion.NetworkProjectConfigAsset");
        const asset = assetClass.method("get_Global").invoke();
        if (asset && !asset.isNull?.()) {
          const list = asset.field("Prefabs").value;
          if (list && !list.isNull?.()) {
            const count = list.method("get_Count").invoke();
            console.log("ConfigAsset.Prefabs count:", count);
            for (let i = 0; i < count; i++) {
              sources.push(list.method("get_Item", 1).invoke(i));
            }
          }
        }
      } catch (e) {
        console.log("ConfigAsset path fail:", e);
      }

      // Path 2: NetworkProjectConfig.get_Global() -> PrefabTable -> get_Prefabs()
      if (sources.length === 0) {
        try {
          const configClass = FusionRuntime.class("Fusion.NetworkProjectConfig");
          const config = configClass.method("get_Global").invoke();
          if (config && !config.isNull?.()) {
            const table = config.field("PrefabTable").value;
            if (table && !table.isNull?.()) {
              const prefabs = table.method("get_Prefabs").invoke();
              const count = prefabs.method("get_Count").invoke();
              console.log("PrefabTable count:", count);
              for (let i = 0; i < count; i++) {
                sources.push(prefabs.method("get_Item", 1).invoke(i));
              }
            }
          }
        } catch (e) {
          console.log("Config path fail:", e);
        }
      }

      console.log("Prefab source count:", sources.length);

      for (let i = 0; i < sources.length; i++) {
        const src = sources[i];
        try {
          if (!src || src.isNull?.()) {
            console.log("[" + i + "] null");
            continue;
          }

          let name = null;

          // Resource source: ResourcePath field
          try {
            const rp = src.field("ResourcePath").value;
            if (rp && !rp.isNull?.()) name = rp.toString();
          } catch (_) {}

          // get_Description()
          if (!name) {
            try {
              const d = src.method("get_Description").invoke();
              if (d && !d.isNull?.()) name = d.toString();
            } catch (_) {}
          }

          // get_Prefab() -> get_name()
          if (!name) {
            try {
              const obj = src.method("get_Prefab").invoke();
              if (obj && !obj.isNull?.()) {
                const n = obj.method("get_name").invoke();
                if (n && !n.isNull?.()) name = n.toString();
              }
            } catch (_) {}
          }

          // AssetGuid
          let guid = "";
          try {
            const g = src.field("AssetGuid").value;
            if (g) guid = " " + g.method("ToString").invoke().toString();
          } catch (_) {}

          console.log("[" + i + "] " + (name ? name : "<" + src.class.name + ">") + guid);
        } catch (e) {
          console.log("[" + i + "] err", e);
        }
      }

      console.log("=== Done ===");
    } catch (e) {
      console.log("Dump Prefab Names error:", e);
    }
  },
  keepOn: false,
}),
    ]
  ];

  let buttonMap: Map<string, ButtonInfo> = new Map();
  buttons.flat().forEach(button => {
    buttonMap.set(button.buttonText, button);
  });

  function getIndex(buttonText: string): ButtonInfo | undefined {
    return buttonMap.get(buttonText);
  }

  const OnTrigMethod = GorillaReportButton.method("OnTriggerEnter");
  OnTrigMethod.implementation = function (collider: any) {
    try {
      const rawName = this.method("get_name").invoke().toString();

      if (rawName.length > 1 && rawName[1] == "@") {
        if (referenceCollider != null && collider.handle.equals(referenceCollider.handle)) {
          const goName = rawName.substring(2, rawName.length - 1);
          const _time = Time.method("get_time").invoke();

          if (_time > buttonClickDelay) {
            buttonClickDelay = _time + 0.2;

            const button = getIndex(goName)
            if (button) {
              if (button.keepOn) {
                button.enabled = !button.enabled;

                if (button?.enabled) {
                  button.enableMethod?.();
                } else {
                  button?.disableMethod?.();
                }

              } else {
                button?.method?.();
              }

              reloadMenu();
            }
          }
        }
      }
    } catch (_) { }
  };

  try {
    const TermKeyClass = AssemblyCSharp.class("AnimalCompany.ComputerTerminalKey");
    const termEnter = TermKeyClass.method("OnTriggerEnter");
    if (!OnTrigMethod.handle.equals(termEnter.handle)) {
      termEnter.implementation = function (_collider: any) { };
    }
    TermKeyClass.method("OnTriggerExit").implementation = function (_collider: any) { };
    TermKeyClass.method("Start").implementation = function () { };
  } catch (e) {
    console.log("terminal key neutralize failed:", e);
  }

  const GTUpdateMethod = GTPlayer.method("Update");

  function onGameUpdate() {

    OVRInputHandler.update();

    leftPrimary = OVRInputHandler.leftControllerPrimaryButton
    leftSecondary = OVRInputHandler.leftControllerSecondaryButton;

    rightPrimary = OVRInputHandler.rightControllerPrimaryButton;
    rightSecondary = OVRInputHandler.rightControllerSecondaryButton;

    leftGrab = OVRInputHandler.leftGrab;
    rightTrigger = OVRInputHandler.rightControllerTriggerButton;

    leftTrigger = OVRInputHandler.leftControllerTriggerButton;
    rightTrigger = OVRInputHandler.rightControllerTriggerButton;

    deltaTime = Time.method("get_deltaTime").invoke();
    time = Time.method("get_time").invoke();

    if (leftSecondary) {
      if (menu == null) {
        renderMenu();
      } else {
        recenterMenu();
      }
    } else {
      if (menu != null) {
        Destroy(menu);
        menu = null;
      }
    }

    if (menu == null) {
      if (reference != null) {
        Destroy(reference);
        reference = null;
      }
    } else {
      if (reference == null) {
        renderReference();
      }
    }

    try {
      if (GunPointer != null) {
        if (!(GunPointer.method("get_activeSelf").invoke())) {
          Destroy(GunPointer);
          GunPointer = null;
        }
        else
          GunPointer.method("SetActive").invoke(false);
      }

      if (GunLine != null) {
        let lineObj = GunLine.method("get_gameObject").invoke();
        if (lineObj != null) {
          if (!(lineObj.method("get_activeSelf").invoke())) {
            Destroy(lineObj);
            GunLine = null;
          }
          else
            lineObj.method("SetActive").invoke(false);
        }
      }
    } catch { }

    if (infAmmoRevolverCock) {
      try {
        const Revolver = Il2Cpp.domain.assembly("AnimalCompany").image.class("AnimalCompany.Revolver");
        const revolvers = Object.method("FindObjectsOfType").inflate(Revolver).invoke();
        for (let i = 0; i < revolvers.length; i++) {
          const rv = revolvers.get ? revolvers.get(i) : revolvers[i];
          if (!rv || rv.isNull?.()) continue;
          try { rv.method("set_isHammerCocked").invoke(true); } catch (e) {}
          try { rv.method("set_ammoLoaded").invoke(255); } catch (e) {}
        }
      } catch (e) {}
    }

    buttons.flat()
      .filter(button => button.enabled)
      .forEach(button => {
        if (button.method) {
          try {
            button.method();
          } catch (error: any) {
            console.error(`Error executing method for button '${button.buttonText || 'unnamed'}':`, error);
            console.error('Error stack:', error.stack);
            console.error('Button object:', button);

            if (error.stack) {
              const stackLines = error.stack.split('\n');
              if (stackLines.length > 1) {
                console.error('Error occurred at:', stackLines[1].trim());
              }
            }
          }
        }
      });

  }

  Interceptor.attach(GTUpdateMethod.virtualAddress, {
    onEnter() {
      try {
        onGameUpdate();
      } catch (e) {
        console.error("update hook error:", e);
      }
    }
  });
  const TopBanner = `    /$$$$$  /$$$$$$  /$$                           /$$      /$$                 /$$ /$$$$$$$$
   |__  $$ /$$$_  $$| $$                          | $$$    /$$$                | $$|_____ $$ 
      | $$| $$$$\\ $$| $$   /$$  /$$$$$$   /$$$$$$ | $$$$  /$$$$  /$$$$$$   /$$$$$$$     /$$/ 
      | $$| $$ $$ $$| $$  /$$/ /$$__  $$ /$$__  $$| $$ $$/$$ $$ /$$__  $$ /$$__  $$    /$$/  
 /$$  | $$| $$\\ $$$$| $$$$$$/ | $$$$$$$$| $$  \\__/| $$  $$$| $$| $$  \\ $$| $$  | $$   /$$/   
| $$  | $$| $$ \\ $$$| $$_  $$ | $$_____/| $$      | $$\\  $ | $$| $$  | $$| $$  | $$  /$$/    
|  $$$$$$/|  $$$$$$/| $$ \\  $$|  $$$$$$$| $$      | $$ \\/  | $$|  $$$$$$/|  $$$$$$$ /$$$$$$$$
 \\______/  \\______/ |__/  \\__/ \\_______/|__/      |__/     |__/ \\______/  \\_______/|________/
`;

  console.log(`Compiled ${new Date().toISOString()}`);
  console.log(TopBanner);
  console.log("THANK YOU FOR USING J0KER CLIENT!");
  console.log("linktr.ee/j0kermodz")

}, "main");

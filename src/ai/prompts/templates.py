"""
TRIZ提示词模板
将40发明原理、76标准解和矛盾求解流程转化为Python内置格式
"""

# 76标准解分类结构（精简版）
# 格式: (class, group, standard) -> {name, description, aim, example}
STANDARD_SOLUTIONS_76 = {
    # Class 1: 构建和分解物质-场模型 (13个标准)
    (1, 1, 1): {
        "name": "构建完整的物质-场模型",
        "aim": "完成工程系统，使其包含两个物质(S1, S2)和一个场(F)",
        "example": "卡车无燃料：S1=卡车, S2=燃料, F=化学→机械能转换"
    },
    (1, 1, 2): {
        "name": "内加法构建复杂物质-场模型",
        "aim": "在现有物质内部引入添加剂(S3)来改善有用效应",
        "example": "焊锡丝内含助焊剂、碳纤维自修复材料"
    },
    (1, 1, 3): {
        "name": "外加法构建复杂物质-场模型",
        "aim": "在物质外部添加添加剂(S3)来改善有用效应",
        "example": "手术手套涂抗病毒涂层、滑雪板打蜡"
    },
    (1, 1, 4): {
        "name": "利用系统环境中的物质",
        "aim": "利用现有环境中的物质作为功能元素",
        "example": "海水中浮标利用水作为缓冲物质"
    },
    (1, 2, 1): {
        "name": "通过第三方物质消除有害效应",
        "aim": "在两个物质间引入第三物质来消除有害效应",
        "example": "齿轮间加润滑剂消除摩擦"
    },

    # Class 2: 改进物质-场模型 (23个标准)
    (2, 1, 1): {
        "name": "增强有用效应",
        "aim": "通过改进系统组件来增强有用效应",
        "example": "增大电机功率提升工具效率"
    },

    # Class 3: 超系统和子系统过渡 (6个标准)
    (3, 1, 1): {
        "name": "过渡到超系统",
        "aim": "将问题转移到大系统中解决",
        "example": "多个相同组件组合成多系统"
    },
    (3, 2, 1): {
        "name": "过渡到子系统",
        "aim": "在微观层面寻找解决方案",
        "example": "使用纳米材料改变宏观属性"
    },

    # Class 4: 检测和测量 (17个标准)
    (4, 1, 1): {
        "name": "间接检测方法",
        "aim": "通过测量相关参数间接获取信息",
        "example": "通过温度间接测量压力"
    },

    # Class 5: 标准解应用辅助 (17个标准)
    (5, 1, 1): {
        "name": "物质添加原则",
        "aim": "优先添加内部物质，再添加外部物质",
        "example": "掺杂半导体、涂覆防腐层"
    },
    (5, 2, 1): {
        "name": "能量传递原则",
        "aim": "利用场来实现能量有效传递",
        "example": "使用电磁场代替机械传动"
    }
}


# 物质-场分析模板
SUFIELD_ANALYSIS_TEMPLATE = """
## 物质-场分析 (Substance-Field Analysis)

### 基本概念
- **物质(S)**: 具有质量的组件（轮子、齿轮、螺丝等）
- **场(F)**: 能量形式（机械场、电场、磁场、热场、化学场等）

### 物质-场模型符号
```
S1 --F--> S2  (有用效应)
S1 --xF--> S2 (有害效应)
```

### 标准解应用流程
1. 描述要解决的问题
2. 列出所有相关物质
3. 创建问题的物质-场模型
4. 选择合适的标准解
5. 应用标准解并创建新模型
6. 描述解决方案

### 5大类76标准解概述

**Class 1: 构建和分解物质-场模型 (13个标准)**
- Group 1.1: 生成物质-场模型
- Group 1.2: 分解物质-场模型

**Class 2: 改进物质-场模型 (23个标准)**
- 增强有用效应
- 消除有害效应

**Class 3: 超系统和子系统过渡 (6个标准)**
- 过渡到超系统
- 过渡到子系统

**Class 4: 检测和测量 (17个标准)**
- 间接检测方法
- 强化测量系统

**Class 5: 标准解应用辅助 (17个标准)**
- 物质添加原则
- 能量传递原则
- 动态化原则

### 应用判断逻辑
```
问题类型？
├─ 测量问题 → Class 4 + Class 5
└─ 非测量问题
   ├─ SFM不完整？ → Standard 1.1.1 + Class 5
   └─ SFM完整
      ├─ 有害效应？ → Group 1.2 + Class 5
      └─ 效应不足？ → Class 2/3 + Class 5
```
"""


# 40发明原理详细内容
# 格式: 编号 -> {name, synonyms, sub_principles}
INVENTIVE_PRINCIPLES = {
    1: {
        "name": "Segmentation",
        "synonyms": "segmenting, decomposition, division, fragmentation",
        "sub_principles": [
            "Divide an object into independent parts: IKEA furniture can be easily assembled by customers.",
            "Make an object easy to disassemble: Toothbrush with replaceable brush head.",
            "Separate an object according to a condition: Foldable table legs.",
            "Increase the degree of segmentation: Fine magnetic powder for better field visibility.",
            "Transition to a micro-level: Ferrofluid creation."
        ]
    },
    2: {
        "name": "Separation",
        "synonyms": "taking out, removal, extraction, detachment, isolation",
        "sub_principles": [
            "Separate or extract a disturbing part: Mechanical pencil with exchangeable lead.",
            "Highlight or separate the only necessary part: Scarecrows to protect crops."
        ]
    },
    3: {
        "name": "Local Quality",
        "synonyms": "local properties, optimal conditions, adaptation, customization",
        "sub_principles": [
            "Transition from homogeneous to inhomogeneous structure: Anti-slip socks with rubber studs.",
            "Different parts perform different functions: Reinforced shoelace ends.",
            "Use each component under optimal conditions: Seamless pipe production with internal guide."
        ]
    },
    4: {
        "name": "Asymmetry",
        "synonyms": "symmetry change",
        "sub_principles": [
            "Transition from symmetrical to asymmetrical forms: Asymmetric connectors for proper insertion.",
            "Increasing asymmetry if it already exists: Asymmetric car tire with fabric reinforcement.",
            "Adapt to asymmetries in environment: Adjustable furniture feet."
        ]
    },
    5: {
        "name": "Merging",
        "synonyms": "coupling, uniting, joining, consolidation, integration",
        "sub_principles": [
            "Spatial grouping of similar objects: Catamaran watercraft.",
            "Temporal coupling of similar processes: Modern lighter with piezo ignition.",
            "Group into bi- or poly-systems: Bicycle chain linkage."
        ]
    },
    6: {
        "name": "Universality",
        "synonyms": "multi-functionality, multi-function",
        "sub_principles": [
            "Object performs multiple functions: All-in-one printer, Swiss Army knife.",
            "Use of standardized features: Universal battery compartment."
        ]
    },
    7: {
        "name": "Nesting",
        "synonyms": "matryoshka dolls, stacking dolls, nested, one in the other",
        "sub_principles": [
            "Object contained within another: Foldable trekking cup.",
            "Object located through cavity of another: Travel toothbrush handle as protective cap.",
            "Telescopic objects: Retractable pointer, car antenna."
        ]
    },
    8: {
        "name": "Anti-weight",
        "synonyms": "weight-compensation, countermass, counterweight, levitation",
        "sub_principles": [
            "Compensate weight by buoyant force: Airplane wings generating lift.",
            "Counterbalance through aerodynamic forces: Cargo drone design.",
            "Reduce mass using environment: Buoyant materials in underwater equipment.",
            "Compensate weight through magnetic forces: Magnetic levitation furniture."
        ]
    },
    9: {
        "name": "Preliminary Anti-action",
        "synonyms": "previous counteraction, advanced counteraction, preload, preventive measures",
        "sub_principles": [
            "Perform required counteraction first: Wind-up toy car.",
            "Precede harmful action with countermeasures: Probiotics with antibiotics.",
            "Provide counter tension in advance: Pre-compressing shaft before bending."
        ]
    },
    10: {
        "name": "Preliminary Action",
        "synonyms": "advance effect, prior action, pretension, prefabrication",
        "sub_principles": [
            "Carry out action in advance: Coffee capsule, pre-assembled furniture.",
            "Arrange objects in advance: Pre-moistened cleaning cloths, pop-up tents."
        ]
    },
    11: {
        "name": "In-advance Cushioning",
        "synonyms": "beforehand cushioning, previously placed cushion, foresight, prevention",
        "sub_principles": [
            "Take countermeasures beforehand: Pressure relief valve, airbag, phone protective case."
        ]
    },
    12: {
        "name": "Equipotentiality",
        "synonyms": "equipotential, equality, shortest path, balance, on-site working",
        "sub_principles": [
            "Work at constant energy potential: Raised tram stop, pizza cutter.",
            "Avoid changes in potential energy: Rolling cabinets.",
            "Avoid fluctuations in parameters: Energy storage systems.",
            "Eliminate tensions: Anti-static wristband."
        ]
    },
    13: {
        "name": "The Other Way Around",
        "synonyms": "reversal, opposite effect, inversion",
        "sub_principles": [
            "Achieve opposite effect: Ink eraser.",
            "Make moving parts fixed and vice versa: Escalator vs treadmill.",
            "Turn object upside down: Cleaning container by injection from below."
        ]
    },
    14: {
        "name": "Spheroidality and Curvature",
        "synonyms": "sphericity, curvilinearity, spherical movements",
        "sub_principles": [
            "Replace straight with curvilinear: Spherical mirror.",
            "Using rollers, balls, spirals: Ball bearing.",
            "Replace linear with rotary movement: Wheel lighter.",
            "Use centrifugal force: Salad spinner."
        ]
    },
    15: {
        "name": "Dynamization",
        "synonyms": "dynamics, adjustability, adaptability, optimization",
        "sub_principles": [
            "Auto-adjust during operation: Adjustable desk, modern stroller.",
            "Divide into optimally arranged elements: Flexible joint, paper fan.",
            "Make immovable object movable: Wireless mouse.",
            "Increase flexibility: Toothbrush flex zone."
        ]
    },
    16: {
        "name": "Partial or Excessive Actions",
        "synonyms": "overdone action, slightly less/slightly more, excess or shortage",
        "sub_principles": [
            "Implement more or less to simplify: Overfilled ink pad, overfilled plaster."
        ]
    },
    17: {
        "name": "Transition to Another Dimension",
        "synonyms": "higher dimension, another dimension, transition to new dimensions",
        "sub_principles": [
            "Transition to higher dimension: Cheese grater (flat to concave).",
            "Multi-layer instead of single: Multi-level windows, kitchen grater.",
            "Tilt or change position: Bundled wood logs, handbell.",
            "Use different side/face: Mirrors for fruit ripening.",
            "Use optical lines on adjacent areas: Solar reflector."
        ]
    },
    18: {
        "name": "Mechanical Vibration",
        "synonyms": "vibration, mechanical oscillations, oscillation",
        "sub_principles": [
            "Cause oscillation: Air jet on conveyor belt for counting.",
            "Increase frequency to ultrasound: Ultrasonic cleaning.",
            "Use resonant frequency: Circuit filters.",
            "Use piezo vibrators: Piezo de-icing for radar spheres.",
            "Use ultrasonic with electromagnetic: Non-invasive surgery."
        ]
    },
    19: {
        "name": "Periodic Action",
        "synonyms": "impulse mode, periodic function, periodic influence",
        "sub_principles": [
            "Replace continuous with periodic: Jackhammer, ABS brakes.",
            "Change frequency: FM transmission, smoke detector with varying tone.",
            "Use pauses for additional actions: Turning tool retraction, CPR ventilation."
        ]
    },
    20: {
        "name": "Continuity of Useful Action",
        "synonyms": "continuity, uninterrupted useful function, continuous action",
        "sub_principles": [
            "Work without interruption: APU in aircraft, self-cleaning filters.",
            "Avoid idleness: Clipless pedals, printer bidirectional printing.",
            "Replace linear with rotational: Paint roller, revolving door."
        ]
    },
    21: {
        "name": "Skipping",
        "synonyms": "fast passage, rushing through, fastest passage",
        "sub_principles": [
            "Perform harmful actions at high speed: High-speed cutting of flexible parts, flip book."
        ]
    },
    22: {
        "name": "Blessing in Disguise",
        "synonyms": "turning harm to good, convert harm into benefit",
        "sub_principles": [
            "Use harmful factors to achieve positive effect: Vaccines, waste heat for heating.",
            "Eliminate harm by combining with harm: Alternating alkali/acid pipes.",
            "Intensify harmful until it ceases to be: Backfire for forest fire."
        ]
    },
    23: {
        "name": "Feedback",
        "synonyms": "feedback, introducing feedback",
        "sub_principles": [
            "Introduce feedback: Check valve, modern heating thermostat.",
            "Modify or reverse feedback: Smart home lighting with color temperature."
        ]
    },
    24: {
        "name": "Intermediary",
        "synonyms": "catalyst, mediator, introduction of mediators",
        "sub_principles": [
            "Use intermediate object: Protective gloves, V-belt for power transmission.",
            "Temporarily connect: Magnetic connector for charging."
        ]
    },
    25: {
        "name": "Self-service",
        "synonyms": "self-organization, self-working",
        "sub_principles": [
            "System serves itself: Lock nut, solar calculator.",
            "Use waste materials: Manure as fertilizer, metal recycling."
        ]
    },
    26: {
        "name": "Copying",
        "synonyms": "use of copies or models",
        "sub_principles": [
            "Use simplified copy: Jewelry replicas, e-books.",
            "Replace with optical/digital representation: Fish counting via photograph.",
            "Use infrared/UV/X-ray: Thermal imaging, X-ray defect detection."
        ]
    },
    27: {
        "name": "Cheap Short-living Objects",
        "synonyms": "short-livedness, inexpensive disposable",
        "sub_principles": [
            "Replace expensive with cheaper: Paper handkerchiefs, disposable razors."
        ]
    },
    28: {
        "name": "Mechanics Substitution",
        "synonyms": "replacing mechanics with fields, use of magnets",
        "sub_principles": [
            "Replace mechanical with optical/acoustic/thermal/chemical: UV banknote verification.",
            "Use electrical/magnetic fields: Laser rangefinder, car key radio transmission.",
            "Replace static with moving fields: Dynamic climate control system.",
            "Use field-activated particles: Magnetic drug delivery nanoparticles."
        ]
    },
    29: {
        "name": "Pneumatics and Hydraulics",
        "synonyms": "pneumo-/hydro constructions, fluidity, fluid system",
        "sub_principles": [
            "Replace heavy parts with gas/liquid: Bubble wrap, air tires, liquid cooling.",
            "Use gaseous/liquid instead of solid: Airbags, hydraulic braking."
        ]
    },
    30: {
        "name": "Flexible Shells and Thin Films",
        "synonyms": "flexible covers, thin films, membranes",
        "sub_principles": [
            "Replace with flexible shells: Flexible plastic bottles, flexible solar panels.",
            "Isolate with thin film: Tea bag, vacuum storage bags.",
            "Increase flexibility: Adjustable orthotics."
        ]
    },
    31: {
        "name": "Porous Materials",
        "synonyms": "porous materials, holes, voids, capillary structures",
        "sub_principles": [
            "Make porous or add porous materials: Foam, sandwich panels, activated carbon.",
            "Fill pores with beneficial substance: Porous rod for alloy addition."
        ]
    },
    32: {
        "name": "Color Changes",
        "synonyms": "change in coloring, optical properties, transparency",
        "sub_principles": [
            "Change color: Red light in darkroom.",
            "Change transparency: Transparent gas tank.",
            "Use color additives: Fading toothbrush bristles, moisture indicator.",
            "Use phosphorescent substances: UV fault diagnosis."
        ]
    },
    33: {
        "name": "Homogeneity",
        "synonyms": "similar materials, uniform composition",
        "sub_principles": [
            "Make interacting objects from same material: Biodegradable bags, wooden dowels."
        ]
    },
    34: {
        "name": "Discarding and Recovering",
        "synonyms": "Regeneration, rejection and regeneration",
        "sub_principles": [
            "Dispose of parts after purpose: Cartridge ejection, solid-fuel rockets.",
            "Restore parts in operation: Break-off knife blade, rechargeable battery."
        ]
    },
    35: {
        "name": "Parameter Changes",
        "synonyms": "changing properties, change of environment, transformation of state",
        "sub_principles": [
            "Change aggregate state: Frozen abrasive grinding, LNG transport.",
            "Change concentration/density: Fuel paste vs liquid alcohol.",
            "Change flexibility: Liquid soap vs solid soap.",
            "Change temperature/volume: Self-cooling beer keg.",
            "Change pressure: Pressure regulator.",
            "Change external medium: Superconducting MRI with liquid nitrogen."
        ]
    },
    36: {
        "name": "Phase Transitions",
        "synonyms": "paradigm shift, liquidity, use of phase changes",
        "sub_principles": [
            "Use effects during phase transitions: Gel heat pack, heat pump."
        ]
    },
    37: {
        "name": "Thermal Expansion",
        "synonyms": "relative change, thermal expansion and compression",
        "sub_principles": [
            "Use thermal expansion: Shrink tubing, liquid thermometer.",
            "Use multiple materials with different coefficients: Leaf spring thermostat."
        ]
    },
    38: {
        "name": "Strong Oxidants",
        "synonyms": "strong oxidizing agents, accelerated oxidation",
        "sub_principles": [
            "Replace air with oxygen-enriched: Oxidizing cleaning agents.",
            "Replace with pure oxygen: Steel production with lance.",
            "Expose to ionizing radiation: Gamma射线 for plastic strengthening.",
            "Use ionized oxygen: Ionizers for air cleaning.",
            "Use ozone: Ozone generators for odor removal."
        ]
    },
    39: {
        "name": "Inert Atmosphere",
        "synonyms": "inert environment, protective environment",
        "sub_principles": [
            "Replace with inert medium: Argon welding, incandescent lamp gas.",
            "Carry out in vacuum: Vacuum packed food.",
            "Add neutral substance: Shaving foam, speaker foam."
        ]
    },
    40: {
        "name": "Composite Materials",
        "synonyms": "composite substances, heterogeneous substances, mixtures",
        "sub_principles": [
            "Replace homogeneous with composite: Carbon fiber reinforced plastics.",
            "Change to composite materials: Tetra Pak multi-layer packaging."
        ]
    }
}


# 39个标准工程参数
ENGINEERING_PARAMETERS_39 = {
    1: "Weight of moving object",
    2: "Weight of stationary object",
    3: "Length of moving object",
    4: "Length of stationary object",
    5: "Area of moving object",
    6: "Area of stationary object",
    7: "Volume of moving object",
    8: "Volume of stationary object",
    9: "Speed",
    10: "Force",
    11: "Stress or pressure",
    12: "Shape",
    13: "Stability of object",
    14: "Strength",
    15: "Durability of moving object",
    16: "Durability of stationary object",
    17: "Temperature",
    18: "Illumination",
    19: "Energy consumption of moving object",
    20: "Energy consumption of stationary object",
    21: "Power",
    22: "Loss of energy",
    23: "Loss of substance",
    24: "Loss of information",
    25: "Loss of time",
    26: "Quantity of substance",
    27: "Quantity of information",
    28: "Reliability",
    29: "Measurement precision",
    30: "Manufacturing precision",
    31: "Object-affected harmful factors",
    32: "Object-created harmful factors",
    33: "Ease of manufacture",
    34: "Ease of operation",
    35: "Ease of repair",
    36: "Adaptability or versatility",
    37: "Device complexity",
    38: "Difficulty of detecting/measuring",
    39: "Extent of automation"
}


# 7步工程矛盾求解流程（详细版）
ALTSHULLER_SOLVING_STEPS = """
## 7-Step Altshuller Matrix Engineering Contradiction Solving Process

### Step 1: Formulate Engineering Contradiction
Express your problem as an engineering contradiction using IF... THEN... BUT... format:
- "IF [you improve feature A], THEN [desired outcome], BUT [undesired consequence]"

### Step 2: Formulate Alternative Contradiction (Verification)
Express the same problem from a different angle:
- Swap the THEN and BUT parts, invert the direction of parameter change

### Step 3: Identify Specific Parameters
From the contradiction:
- Improving parameter is found AFTER "THEN"
- Worsening parameter is found AFTER "BUT"

### Step 4: Generalize to Typical Parameters
Map your specific parameters to the 39 standard Altshuller parameters:

| # | Parameter | # | Parameter |
|---|-----------|---|-----------|
| 1 | Weight of moving object | 21 | Power |
| 2 | Weight of stationary object | 22 | Loss of energy |
| 3 | Length of moving object | 23 | Loss of substance |
| 4 | Length of stationary object | 24 | Loss of information |
| 5 | Area of moving object | 25 | Loss of time |
| 6 | Area of stationary object | 26 | Quantity of substance |
| 7 | Volume of moving object | 27 | Quantity of information |
| 8 | Volume of stationary object | 28 | Reliability |
| 9 | Speed | 29 | Measurement precision |
| 10 | Force | 30 | Manufacturing precision |
| 11 | Stress or pressure | 31 | Object-affected harmful factors |
| 12 | Shape | 32 | Object-created harmful factors |
| 13 | Stability | 33 | Ease of manufacture |
| 14 | Strength | 34 | Ease of operation |
| 15 | Durability (moving) | 35 | Ease of repair |
| 16 | Durability (stationary) | 36 | Adaptability |
| 17 | Temperature | 37 | Device complexity |
| 18 | Illumination | 38 | Difficulty of detecting |
| 19 | Energy consumption (moving) | 39 | Extent of automation |
| 20 | Energy consumption (stationary) | | |

### Step 5: Matrix Lookup
Use the Altshuller Contradiction Matrix to find recommended inventive principles:
- Row = Improving parameter
- Column = Worsening parameter
- Intersection = Recommended principle numbers (1-40)

### Step 6: Study Principles in Detail
For each recommended principle, consult the 40 Inventive Principles:
- Consider synonyms and sub-principles
- Review practical examples
- Note: If matrix shows "no preferred principles", consider all 40

### Step 7: Generate Concrete Solutions
Based on the principles, propose specific solutions:
- Explain WHY each solution applies the principle
- Consider component-level, system-level, and environment-level applications

## Example: Backpack Problem
**Problem**: Large backpack but lightweight

**Step 1**: IF backpack is large THEN can carry more books BUT increases back fatigue

**Step 2**: IF backpack is small THEN less fatigue BUT less storage

**Step 3**: Improving = "Volume", Worsening = "Ease of operation"

**Step 4**: Improving = #8 Volume of stationary object, Worsening = #34 Ease of operation

**Step 5**: Matrix lookup → Principles #7 (Nesting), #2 (Separation), #35 (Parameter Changes)

**Step 7**: Solutions using nesting (compartmentalized backpack), separation (detachable compartments), parameter changes (lighter materials)
"""


# 矛盾求解指令模板
CONTRADICTION_SOLVER_TEMPLATE = """You are a TRIZ expert specializing in solving engineering and physical contradictions.

## Your Task
Help the user analyze and solve technical problems using TRIZ (Theory of Inventive Problem Solving) methodology.

## Engineering Contradiction Format
When identifying an engineering contradiction, use this format:
**IF** you improve [feature A], **THEN** [desired outcome], **BUT** [undesired consequence]

Example: "IF the engine gets stronger, THEN the car goes faster, BUT fuel consumption increases"

## Physical Contradiction Format
When identifying a physical contradiction, use this format:
[Parameter] must be [value 1] TO [benefit], AND [parameter] must be [value 2] TO [benefit]

Example: "The boat must be wide TO prevent capsizing, AND narrow TO go fast"

""" + ALTSHULLER_SOLVING_STEPS + """

## Analysis Process
1. Ask the user to describe their problem or system
2. Help formulate the contradiction
3. Apply the appropriate TRIZ tools
4. Generate specific, practical solutions

## Output Format
Present solutions with:
- Principle applied
- How to implement it
- Practical examples
"""


# 解决方案生成模板
SOLUTION_GENERATION_TEMPLATE = """你是TRIZ创新方法专家。请根据以下信息，针对具体问题生成可操作的技术解决方案。

**问题背景：** {problem}

**技术矛盾：**
- 改善参数: {improving_param}
- 恶化参数: {worsening_param}

**推荐的发明原理：**
{principles_text}

## 输出格式要求（严格遵守）

直接输出JSON数组，不要用```包裹，不要任何前缀或后缀文字！

JSON格式：
[
  {{
    "principle_id": 原理编号（1-40的整数）,
    "principle_name": "原理名称",
    "technical_solution": "【技术方案】（50-100字）具体技术实现步骤，如何降低{worsening}同时提升{improving}",
    "innovation_point": "【创新点】（20-30字）具体技术创新点",
    "cross_domain_cases": ["领域A:具体案例", "领域B:具体案例"],
    "expected_effect": "【效果】量化指标，如：效率提升X%",
    "confidence": 0.0到1.0之间的置信度
  }}
]

规范：
1. technical_solution：50-100字，具体技术步骤
2. innovation_point：20-30字，具体创新
3. cross_domain_cases：2个案例
4. expected_effect：量化指标
5. 直接输出JSON，不要Markdown包裹！"""



# 功能分析模板
FUNCTION_ANALYSIS_TEMPLATE = """You are a TRIZ expert specializing in Function Analysis of technical systems.

## Your Task
Guide users through a structured Function Analysis to identify tools, actions, objects, and functions, clarify component relationships, and reveal opportunities for improvement.

## Function Definition
A function is an action performed by one component (the TOOL) to change or maintain a parameter of another component (the OBJECT).
- Broom moves dirt
- Helmet stops stone
- Display informs user

## Component Analysis
For the technical system under analysis:
1. **Super-system**: External components that interact with the system
2. **Technical system**: The core system being analyzed
3. **Sub-system**: Components within the technical system

## Function Classification
| Category | Description | Assessment |
|----------|-------------|------------|
| U (Useful) | Function contributes to the main function | Normal (N), Insufficient (I), Excessive (E) |
| H (Harmful) | Function degrades or damages | Marked as "---" |

## Magic Wand Test
To verify if a function is legitimate: "If you remove the tool, does the object change?"
- If YES → Function exists
- If NO → No function (coincidence)

## Function Analysis Table Format
| Tool | Action | Object | Category (U/H) | Degree (N/I/E/---) | Changed Parameter |

## Main Function Identification
The main function always targets a component in the SUPER-SYSTEM:
- Airplane main function: Transport passengers → targets passengers → changes geographic location

## Analysis Process
1. Ask: "What is your technical system?"
2. Conduct component analysis (super-system, system, sub-system)
3. Analyze interactions between components
4. Create function table with Tool | Action | Object | Category | Degree | Parameter
5. Identify main function and harmful functions
6. Propose improvements

## Example: Electric Drill
**Components:**
- Super-system: User, power source, workpiece
- System: Electric drill
- Sub-system: Motor, chuck, trigger, housing

**Functions:**
| Tool | Action | Object | Category | Degree | Parameter |
|------|--------|--------|----------|--------|-----------|
| Drill | rotates | Chuck | U | N | Rotation |
| Chuck | holds | Bit | U | N | Position |
| Trigger | controls | Motor | U | N | Power |
| Motor | produces | Torque | U | I | Torque |
| Housing | protects | User | U | N | Safety |
"""


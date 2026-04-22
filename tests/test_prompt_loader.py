"""
TRIZ提示词模块测试
"""

from src.ai.prompts import PromptBuilder, PromptLoader


class TestPromptLoader:
    """提示词加载器测试"""

    def test_get_principle(self):
        """测试获取单个原理"""
        loader = PromptLoader()
        p1 = loader.get_principle(1)
        assert p1 is not None
        assert p1["name"] == "分割原理"
        assert "synonyms" in p1
        assert "sub_principles" in p1

    def test_get_principle_invalid_id(self):
        """测试获取无效编号"""
        loader = PromptLoader()
        assert loader.get_principle(0) is None
        assert loader.get_principle(41) is None

    def test_get_principle_name(self):
        """测试获取原理名称"""
        loader = PromptLoader()
        assert loader.get_principle_name(1) == "分割原理"
        assert loader.get_principle_name(2) == "抽取原理"
        assert loader.get_principle_name(40) == "复合材料原理"

    def test_get_all_principles(self):
        """测试获取所有原理"""
        loader = PromptLoader()
        all_p = loader.get_all_principles()
        assert len(all_p) == 40
        assert 1 in all_p
        assert 40 in all_p

    def test_build_principle_detail(self):
        """测试构建原理详情"""
        loader = PromptLoader()
        detail = loader.build_principle_detail(1)
        assert "#1" in detail
        assert "分割原理" in detail

    def test_build_principles_text(self):
        """测试构建多个原理文本"""
        loader = PromptLoader()
        text = loader.build_principles_text([1, 2, 3])
        assert "#1" in text
        assert "#2" in text
        assert "#3" in text
        assert "分割原理" in text

    def test_build_principles_text_empty(self):
        """测试空原理列表"""
        loader = PromptLoader()
        text = loader.build_principles_text([])
        assert "No specific principles" in text

    def test_get_39_parameters(self):
        """测试获取39参数"""
        loader = PromptLoader()
        params = loader.get_39_parameters()
        assert len(params) == 39
        assert params[1] == "Weight of moving object"
        assert params[9] == "Speed"
        assert params[39] == "Extent of automation"

    def test_get_parameter_name(self):
        """测试获取单个参数名称"""
        loader = PromptLoader()
        assert loader.get_parameter_name(1) == "Weight of moving object"
        assert loader.get_parameter_name(0) == ""
        assert loader.get_parameter_name(40) == ""

    def test_get_39_parameters_text(self):
        """测试获取39参数可读文本"""
        loader = PromptLoader()
        text = loader.get_39_parameters_text()
        assert "39 Standard Altshuller Parameters" in text
        assert "Weight of moving object" in text

    def test_get_altshuller_solving_steps(self):
        """测试获取7步求解流程"""
        loader = PromptLoader()
        steps = loader.get_altshuller_solving_steps()
        assert "Step 1" in steps
        assert "Step 7" in steps
        assert "Altshuller Matrix" in steps

    def test_get_function_analysis_template(self):
        """测试获取功能分析模板"""
        loader = PromptLoader()
        fa = loader.get_function_analysis_template()
        assert "Function Analysis" in fa
        assert "Tool" in fa
        assert "Object" in fa
        assert "Super-system" in fa


class TestPromptBuilder:
    """提示词构建器测试"""

    def test_build_solution_prompt(self):
        """测试构建解决方案提示词（4字段结构）"""
        builder = PromptBuilder()
        prompt = builder.build_solution_prompt(
            problem="手机需要更大电池但要保持轻薄",
            improving_param="能量消耗",
            worsening_param="重量",
            principles=[1, 2, 35],
            solution_count=3,
        )
        assert len(prompt) > 700  # 提示词应该足够长
        assert "手机需要更大电池" in prompt
        assert "能量消耗" in prompt
        # 验证4字段结构
        assert "technical_solution" in prompt or "技术方案" in prompt
        assert "innovation_point" in prompt or "创新点" in prompt
        assert "cross_domain_cases" in prompt or "领域" in prompt
        assert "expected_effect" in prompt or "效果" in prompt

    def test_build_solution_prompt_no_principles(self):
        """测试无原理时的提示词"""
        builder = PromptBuilder()
        prompt = builder.build_solution_prompt(
            problem="测试问题", principles=[], solution_count=3
        )
        assert "测试问题" in prompt
        assert "未指定" in prompt

    def test_build_contradiction_prompt(self):
        """测试构建矛盾分析提示词"""
        builder = PromptBuilder()
        prompt = builder.build_contradiction_prompt(
            problem="汽车发动机需要更强动力",
            improving_param="速度",
            worsening_param="油耗",
            principles=[1, 2],
        )
        assert "汽车发动机需要更强动力" in prompt
        assert "TRIZ expert" in prompt
        assert "速度" in prompt

    def test_build_parameter_detection_prompt(self):
        """测试参数检测提示词"""
        builder = PromptBuilder()
        prompt = builder.build_parameter_detection_prompt("手机屏幕太亮")
        assert "手机屏幕太亮" in prompt
        assert "改善参数" in prompt
        assert "JSON" in prompt

    def test_get_contradiction_format_guide(self):
        """测试矛盾格式指南"""
        builder = PromptBuilder()
        guide = builder.get_contradiction_format_guide()
        assert "IF" in guide
        assert "BUT" in guide
        assert "物理矛盾" in guide

    def test_build_function_analysis_prompt(self):
        """测试构建功能分析提示词"""
        builder = PromptBuilder()
        prompt = builder.build_function_analysis_prompt()
        assert "Function Analysis" in prompt
        assert len(prompt) > 2000

        prompt_with_system = builder.build_function_analysis_prompt("Electric Drill")
        assert "Electric Drill" in prompt_with_system

    def test_get_standard_solution(self):
        """测试获取标准解"""
        loader = PromptLoader()
        sol = loader.get_standard_solution(1, 1, 1)
        assert sol is not None
        assert "构建完整的物质-场模型" in sol["name"]

    def test_get_all_standard_solutions(self):
        """测试获取所有标准解"""
        loader = PromptLoader()
        solutions = loader.get_all_standard_solutions()
        assert len(solutions) > 0

    def test_get_standard_solutions_by_class(self):
        """测试按类别获取标准解"""
        loader = PromptLoader()
        class1 = loader.get_standard_solutions_by_class(1)
        assert len(class1) > 0
        assert all(k[0] == 1 for k in class1.keys())

    def test_get_subfield_analysis_template(self):
        """测试获取物质-场分析模板"""
        loader = PromptLoader()
        sf = loader.get_subfield_analysis_template()
        assert "物质-场" in sf or "Substance-Field" in sf

    def test_build_subfield_analysis_prompt(self):
        """测试构建物质-场分析提示词"""
        builder = PromptBuilder()
        prompt = builder.build_subfield_analysis_prompt()
        assert "Substance-Field" in prompt or "物质-场" in prompt

        prompt_with_problem = builder.build_subfield_analysis_prompt("齿轮噪音问题")
        assert "齿轮噪音问题" in prompt_with_problem

    def test_build_standard_solutions_prompt(self):
        """测试构建标准解提示词"""
        builder = PromptBuilder()
        prompt = builder.build_standard_solutions_prompt("减少磨损")
        assert "Standard Solutions" in prompt or "标准解" in prompt

        prompt_with_class = builder.build_standard_solutions_prompt(
            "减少磨损", solution_class=2
        )
        assert "Class 2" in prompt_with_class

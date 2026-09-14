from __future__ import annotations

import re

from latex2mathml.converter import convert as latex_to_mathml
from lxml import etree
from mathml2omml import convert as mathml_to_omml

MATH_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
DRAWING_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
DRAWING_2010_NS = "http://schemas.microsoft.com/office/drawing/2010/main"

_MATH_SIGNAL = re.compile(
    r"(?:\\(?:frac|sqrt|sum|pm|times|approx|neq|leq|geq|implies|rho|pi|sigma|Delta)\b"
    r"|->|[=±×÷≈≠≤≥√∑∝^]|\b(?:rho|pi|sigma|delta)\b)",
    flags=re.IGNORECASE,
)
_TOKEN = re.compile(
    r"(->|<=|>=|!=|\+/-|\\[A-Za-z]+|[A-Za-z]+|\d+(?:\.\d+)?|\s+|.)"
)
_GREEK = {
    "alpha": r"\alpha",
    "beta": r"\beta",
    "delta": r"\Delta",
    "epsilon": r"\epsilon",
    "lambda": r"\lambda",
    "mu": r"\mu",
    "omega": r"\Omega",
    "pi": r"\pi",
    "rho": r"\rho",
    "sigma": r"\sigma",
    "theta": r"\theta",
}
_OPERATORS = {
    "->": r"\rightarrow",
    "<=": r"\leq",
    ">=": r"\geq",
    "!=": r"\neq",
    "+/-": r"\pm",
    "±": r"\pm",
    "×": r"\times",
    "÷": r"\div",
    "≈": r"\approx",
    "≠": r"\neq",
    "≤": r"\leq",
    "≥": r"\geq",
    "√": r"\sqrt",
    "∑": r"\sum",
    "∝": r"\propto",
    "→": r"\rightarrow",
    "*": r"\,",
}
_WORD_OPERATORS = {
    "approx": r"\approx",
    "sqrt": r"\sqrt",
    "sum": r"\sum",
}
_UNITS = {
    "a",
    "cm",
    "g",
    "j",
    "kg",
    "m",
    "mm",
    "ms",
    "n",
    "s",
    "v",
}


class OfficeMathError(RuntimeError):
    """Raised when an equation cannot be emitted as native Office Math."""


def looks_like_math(text: str) -> bool:
    return bool(_MATH_SIGNAL.search(text))


def _escaped_text(text: str) -> str:
    return text.replace("\\", r"\textbackslash ").replace("{", r"\{").replace("}", r"\}")


def _normalize_sqrt_calls(text: str) -> str:
    """Turn ASCII sqrt(...) calls into LaTeX radicals with balanced scope."""
    result: list[str] = []
    cursor = 0
    while match := re.search(r"\bsqrt\s*\(", text[cursor:], flags=re.IGNORECASE):
        start = cursor + match.start()
        opening = cursor + match.end() - 1
        depth = 1
        closing = opening + 1
        while closing < len(text) and depth:
            depth += (text[closing] == "(") - (text[closing] == ")")
            closing += 1
        if depth:
            break
        result.append(text[cursor:start])
        result.append(r"\sqrt{" + _normalize_sqrt_calls(text[opening + 1 : closing - 1]) + "}")
        cursor = closing
    result.append(text[cursor:])
    return "".join(result)


def _normalize_ascii_notation(text: str) -> str:
    text = _normalize_sqrt_calls(text)
    text = re.sub(r"\b([A-Za-z])_bar\b", r"\\bar{\1}", text)
    superscripts = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻", "0123456789+-")
    subscripts = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
    text = re.sub(
        r"[⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻]+",
        lambda match: "^{" + match.group().translate(superscripts) + "}",
        text,
    )
    return re.sub(
        r"[₀₁₂₃₄₅₆₇₈₉]+",
        lambda match: "_{" + match.group().translate(subscripts) + "}",
        text,
    )


def visible_math_to_latex(text: str) -> str:
    """Convert a mixed human-readable formula line into conservative LaTeX math."""
    text = _normalize_ascii_notation(text.strip())
    output: list[str] = []
    for token in _TOKEN.findall(text):
        if token.isspace():
            # mathml2omml drops MathML spacing elements. A text-space survives
            # conversion as a non-breaking space in a native OfficeMath run.
            output.append(r"\text{ }")
            continue
        if token in _OPERATORS:
            output.append(_OPERATORS[token])
            continue
        if token == "%":
            output.append(r"\%")
            continue
        if re.fullmatch(r"[A-Za-z]+", token):
            lowered = token.casefold()
            if lowered in _GREEK:
                output.append(_GREEK[lowered])
            elif lowered in _WORD_OPERATORS:
                output.append(_WORD_OPERATORS[lowered])
            elif len(token) == 1:
                output.append(token)
            elif lowered in _UNITS:
                output.append(rf"\mathrm{{{token}}}")
            else:
                output.append(rf"\text{{{_escaped_text(token)}}}")
            continue
        output.append(token)
    return "".join(output)


def latex_to_omml(latex: str) -> etree._Element:
    try:
        mathml = latex_to_mathml(latex.strip())
        omml = mathml_to_omml(mathml)
        # mathml2omml 0.0.2 omits this closing tag for mover accents,
        # notably LaTeX ``\bar``. Its later groupChr closing tag is present.
        omml = omml.replace(
            "</m:groupChr><m:e>",
            "</m:groupChrPr><m:e>",
        )
        if "xmlns:m=" not in omml:
            omml = omml.replace("<m:oMath", f'<m:oMath xmlns:m="{MATH_NS}"', 1)
        converted = etree.fromstring(omml.encode("utf-8"))
    except (ValueError, etree.Error, TypeError) as exc:
        raise OfficeMathError(f"Cannot convert equation to Office Math: {latex!r}") from exc
    # A bar is semantically an OMML bar, not a generic group character. The
    # upstream converter emits the latter and PowerPoint positions it poorly.
    for group in list(converted.findall(f".//{{{MATH_NS}}}groupChr")):
        char = group.find(f".//{{{MATH_NS}}}chr")
        if char is None or char.get(f"{{{MATH_NS}}}val") != "¯":
            continue
        parent = group.getparent()
        bar = etree.Element(etree.QName(MATH_NS, "bar"))
        bar_properties = etree.SubElement(bar, etree.QName(MATH_NS, "barPr"))
        position = etree.SubElement(bar_properties, etree.QName(MATH_NS, "pos"))
        position.set(etree.QName(MATH_NS, "val"), "top")
        expression = group.find(f"{{{MATH_NS}}}e")
        if expression is not None:
            bar.append(expression)
        parent.replace(group, bar)
    return converted


def set_native_math_paragraph(
    paragraph,
    latex: str,
    *,
    font_size_pt: int = 20,
    alignment: str = "left",
) -> None:
    """Replace a python-pptx paragraph with editable PowerPoint OfficeMath."""
    omml = latex_to_omml(latex)
    if etree.QName(omml).localname == "oMath":
        math_para = etree.Element(etree.QName(MATH_NS, "oMathPara"))
        math_para.append(omml)
    else:
        math_para = omml

    para_props = math_para.find(f"{{{MATH_NS}}}oMathParaPr")
    if para_props is None:
        para_props = etree.Element(etree.QName(MATH_NS, "oMathParaPr"))
        math_para.insert(0, para_props)
    justification = para_props.find(f"{{{MATH_NS}}}jc")
    if justification is None:
        justification = etree.SubElement(para_props, etree.QName(MATH_NS, "jc"))
    justification.set(etree.QName(MATH_NS, "val"), alignment)

    wrapper = etree.Element(
        etree.QName(DRAWING_2010_NS, "m"),
        nsmap={"a14": DRAWING_2010_NS, "m": MATH_NS},
    )
    wrapper.append(math_para)

    xml_paragraph = paragraph._p
    paragraph_properties = xml_paragraph.find(f"{{{DRAWING_NS}}}pPr")
    for child in list(xml_paragraph):
        if child is not paragraph_properties:
            xml_paragraph.remove(child)
    xml_paragraph.append(wrapper)
    end_properties = etree.SubElement(xml_paragraph, etree.QName(DRAWING_NS, "endParaRPr"))
    end_properties.set("lang", "en-GB")
    end_properties.set("sz", str(font_size_pt * 100))

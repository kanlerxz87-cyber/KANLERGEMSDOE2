"""Guard the most frequently reused small-text colors on the two dashboards.

These checks complement, rather than replace, a browser/axe accessibility audit.
"""
from pathlib import Path
import re

import pytest

ROOT = Path(__file__).resolve().parents[1]


def contrast(foreground, background):
    def luminance(value):
        rgb = [int(value[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        linear = [x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4 for x in rgb]
        return sum(c * v for c, v in zip((.2126, .7152, .0722), linear))
    a, b = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (a + .05) / (b + .05)


def foreground(css, selector):
    rule = re.search(r'(?:^|})\s*' + re.escape(selector) + r'\{([^{}]*)\}', css)
    assert rule, f'missing CSS selector {selector}'
    match = re.search(r'(?:^|;)color:(#[0-9a-fA-F]{6})(?:;|$)', rule.group(1))
    assert match, f'{selector} needs an explicit six-digit foreground color'
    return match.group(1)


@pytest.mark.parametrize(('stylesheet', 'selector', 'background'), [
    ('site.css', '.brand-sub', '#f8f8f2'),
    ('site.css', '.eyebrow', '#eaeee4'),
    ('site.css', '.metric-number', '#fffefa'),
    ('site.css', '.rule-list li span', '#fffefa'),
    ('site.css', 'th', '#f2f5ef'),
    ('site.css', '.subtext', '#fffefa'),
    ('site.css', '.footnote', '#fafbf7'),
    ('site.css', '.feed-item span', '#fffefa'),
    ('site.css', '.source-link small', '#fffefa'),
    ('styles.css', '.topline', '#f6f7f3'),
    ('styles.css', '.topline i', '#f6f7f3'),
    ('styles.css', '.footnote', '#f6f7f3'),
    ('styles.css', '.steps small', '#e9eee4'),
    ('styles.css', '.callout span', '#f8faf4'),
    ('styles.css', 'thead th', '#fafbf8'),
    ('styles.css', '.table-note', '#f6f7f3'),
    ('styles.css', '.next-grid article>span', '#ffffff'),
    ('styles.css', '.source-bar .micro', '#f6f7f3'),
    ('styles.css', '.source-bar p', '#f6f7f3'),
    ('styles.css', '.footer', '#f6f7f3'),
    ('styles.css', '.scroll-hint', '#f6f7f3'),
])
def test_dashboard_small_text_meets_wcag_aa(stylesheet, selector, background):
    css = (ROOT / 'docs/assets' / stylesheet).read_text()
    fg = foreground(css, selector)
    assert contrast(fg, background) >= 4.5, (stylesheet, selector, fg, background)


def test_muted_text_on_k2_tinted_section():
    css = (ROOT / 'docs/assets/site.css').read_text()
    match = re.search(r'--muted:(#[0-9a-fA-F]{6})', css)
    assert match and contrast(match.group(1), '#eaeee4') >= 4.5


@pytest.mark.parametrize(('selector', 'background'), [
    ('.brand small', '#ffffff'),
    ('.stat-label', '#ffffff'),
    ('.stat-grid small', '#ffffff'),
    ('.section-heading>p', '#f6f8f4'),
    ('thead th', '#f9fbf8'),
    ('td small', '#ffffff'),
    ('.proof-card p,.site-card p', '#ffffff'),
    ('.footer-inner', '#ffffff'),
])
def test_decision_desk_small_text_meets_wcag_aa(selector, background):
    css = (ROOT / 'docs/style.css').read_text()
    fg = foreground(css, selector)
    assert contrast(fg, background) >= 4.5, (selector, fg, background)

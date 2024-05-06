"""
Functional tests. NOTE: the server must be running at HOST_BASE for these
tests to pass.
"""
import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from nose.tools import set_trace as nose_trace

HOST_BASE = "http://localhost:6543"

class FunctionalTests(unittest.TestCase):
    def setUp(self):
        self.driver = webdriver.Firefox()

    def test_root(self):
        self.driver.get(HOST_BASE + '/')
        self.assertEqual(self.driver.title, 'Haemosphere')

    def test_search_for_gene_and_view_expression_profile(self):
        self.driver.get(HOST_BASE + '/searches')
        searchbox = self.driver.find_element_by_css_selector("#searchString")
        searchbox.send_keys("myb")
        submit = self.driver.find_element_by_css_selector("#submitKeywordSearch")
        submit.click()

        # wait 5sec for the gene list to load, then select Myb
        expression_link = WebDriverWait(self.driver, 5).until(
            expected_conditions.presence_of_element_located((By.LINK_TEXT, "Myb"))
        )
        expression_link.click()
        # check that graph and legend have loaded
        graph = self.driver.find_element_by_css_selector("#expression-div svg")
        legend = self.driver.find_element_by_css_selector("#legend-div svg")
        # examine checkboxes
        rotate_checkbox, colour_checkbox, showpoints_checkbox = self.driver.find_elements_by_css_selector("#controlPanelDiv input[type='checkbox']")
        self.assertFalse(rotate_checkbox.is_selected())
        self.assertFalse(colour_checkbox.is_selected())
        self.assertTrue(showpoints_checkbox.is_selected())

    def test_search_for_gene_view_expression_find_similar(self):
        self.driver.get(HOST_BASE + '/searches')
        searchbox = self.driver.find_element_by_css_selector("#searchString")
        searchbox.send_keys("myb")
        submit = self.driver.find_element_by_css_selector("#submitKeywordSearch")
        submit.click()

        # wait 5sec for the gene list to load, then select Myb
        expression_link = WebDriverWait(self.driver, 5).until(
            expected_conditions.presence_of_element_located((By.LINK_TEXT, "Myb"))
        )
        expression_link.click()

        # tricky - move the mouse to the svg overlay path, then click
        overlay = self.driver.find_elements_by_css_selector("#expression-div svg g.series path.overlayedPath")[0]
        ActionChains(self.driver).move_to_element_with_offset(overlay, overlay.rect['width']/2, 0).perform()
        while not overlay.is_displayed():
            ActionChains(self.driver).move_by_offset(0, 1).perform()
        ActionChains(self.driver).click().perform()

        # now we can click the 'find similar' link
        self.driver.find_element_by_link_text("find similar").click()

    def tearDown(self):
        self.driver.quit()

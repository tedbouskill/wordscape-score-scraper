from xml.dom.minidom import Element
from lxml import etree
import re

class XMLHelpers:
    @staticmethod
    def extract_namespaces_from_root(root: Element) -> dict[str, str]:
        return {k if k is not None else '': v for k, v in root.nsmap.items()}

    @staticmethod
    def is_valid_xml_element(element: Element) -> bool:
        """
        Check if the given element is a valid XML element (not a processing instruction or other non-standard content).
        """
        return isinstance(element.tag, str)  # Ensure element tag is a string (not None or a special type)

    @staticmethod
    def replace_pi_in_text(text: str, place_holder: str = "") -> str:
        """
        Remove any processing instructions like <?...?> embedded in text content.
        """
        if text:
            try:
                # Replace processing instructions with a placeholder
                return re.sub(r"<\?.*?\?>", place_holder, text)
            except re.error as e:
                print(f"Regex error: {e} with text {text}")
                return text
        return text

    @staticmethod
    def extract_tag_and_attributes(element: Element) -> tuple[str, dict[str, str]]:
        attributes = {k: v for k, v in element.attrib.items() if not k.startswith('{http://www.w3.org/2000/xmlns/}')}
        return element.tag, attributes

    @staticmethod
    def replace_ns(tag: Element, namespaces: dict[str, str]) -> str:
        # First, try to replace with non-default namespaces
        for prefix, uri in namespaces.items():
            if prefix is not None and tag.startswith(f"{{{uri}}}"):
                return tag.replace(f"{{{uri}}}", f"{prefix}:")
        # If no non-default namespace matches, try to replace with the default namespace
        for prefix, uri in namespaces.items():
            if prefix is None and tag.startswith(f"{{{uri}}}"):
                return tag.replace(f"{{{uri}}}", "")
        return tag

    @staticmethod
    def replace_element_with_formatted_text(parent: Element, element: Element, format_string: str) -> None:
        index = parent.index(element)
        tail = element.tail  # Save the tail text of the element being replaced
        parent.remove(element)
        # Insert the formatted text directly in place of the removed element
        if index == 0:
            parent.text = (parent.text or "") + format_string
            # Append the tail of the replaced element to the parent text
            parent.text += tail or ""
        else:
            previous = parent[index - 1]
            previous.tail = (previous.tail or "") + format_string
            # Append the tail of the replaced element to the previous element's tail
            previous.tail += tail or ""


    @staticmethod
    def has_text_content(element: Element) -> bool:
        if element.text and element.text.strip():
            return True
        for child in element:
            if XMLHelpers.has_text_content(child):
                return True
        if element.tail and element.tail.strip():
            return True
        return False

    @staticmethod
    def is_empty_element(element: Element) -> bool:
        # Check if the element has no child elements
        has_no_children = len(element) == 0
        # Check if the element's text is None or empty after being stripped
        has_no_text = not (element.text and element.text.strip())
        # Check if the element's tail text is None or empty after being stripped
        has_no_tail = not (element.tail and element.tail.strip())
        # Return True if all conditions are met
        return has_no_children and has_no_text and has_no_tail

    @staticmethod
    def remove_element_and_contents(tag: Element) -> None:
        parent = tag.getparent()
        if parent is not None:
            # Move the tail text to the previous sibling or parent
            if tag.tail:
                index = parent.index(tag)
                if index > 0:
                    previous = parent[index - 1]
                    if previous.tail:
                        previous.tail += tag.tail
                    else:
                        previous.tail = tag.tail
                else:
                    if parent.text:
                        parent.text += tag.tail
                    else:
                        parent.text = tag.tail

            # Finally, remove the tag and all its contents
            parent.remove(tag)

            # Strip leading/trailing whitespace from the parent's text
            if parent.text:
                parent.text = parent.text.strip()

    @staticmethod
    def remove_elements_and_contents(tags: list[Element]) -> int:
        nb_removed = 0
        for tag in tags:
            nb_removed += 1
            XMLHelpers.remove_element_and_contents(tag)
        return nb_removed

    @staticmethod
    def remove_element_preserve_text(tag: etree.Element) -> None:
        parent = tag.getparent()
        if parent is not None:
            # Find the index of the tag in the parent's children
            index = parent.index(tag)

            # Insert the text before the tag
            if tag.text:
                if index > 0:
                    previous = parent[index - 1]
                    if previous.tail:
                        previous.tail += tag.text
                    else:
                        previous.tail = tag.text
                else:
                    if parent.text:
                        parent.text += tag.text
                    else:
                        parent.text = tag.text

            # Insert the children of the tag at the correct position
            for child in tag:
                parent.insert(index, child)
                index += 1

            # Move the tail text to the previous sibling or parent
            if tag.tail:
                if index > 0:
                    previous = parent[index - 1]
                    if previous.tail:
                        previous.tail += tag.tail
                    else:
                        previous.tail = tag.tail
                else:
                    if parent.text:
                        parent.text += tag.tail
                    else:
                        parent.text = tag.tail

            # Finally, remove the tag
            parent.remove(tag)

    @staticmethod
    def remove_elements_preserve_text(tags: list[Element]) -> int:
        nb_removed = 0
        for tag in tags:
            nb_removed += 1
            XMLHelpers.remove_element_preserve_text(tag)
        return nb_removed

    @staticmethod
    def has_only_text(element: Element) -> bool:
        return len(element) == 0 and element.text is not None and element.text.strip() != ''

    @staticmethod
    def normalize_text(text: str) -> str:
        result = re.sub(r'\s+', ' ', text).strip()
        return result

    @staticmethod
    def extract_all_nested_text(element: Element) -> str:
        # Extract full text from the element, including nested OCRConfidenceData
        text = ''.join(element.xpath('.//text()')).strip()

        # Remove linefeeds and extra spaces
        cleaned_header_text = ' '.join(text.replace('\n', ' ').split()).strip()

        return cleaned_header_text

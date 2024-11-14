from datetime import datetime
from typing import List
import ifcopenshell
import ifcopenshell.util.element


class Patcher:
    def __init__(self, files: List[str]):
        self.result = None
        self.files = files
        self.num_files = len(files)

    def patch(self):
        if len(self.files) == 0:
            return self.result
        if not self.result and len(self.files) > 1:
            self.result = ifcopenshell.open(self.files.pop())

        model_2 = ifcopenshell.open(self.files.pop())
        print(f"merging {self.num_files - len(self.files)} / {self.num_files}...")

        self.existing_contexts = self.result.by_type("IfcGeometricRepresentationContext")
        self.added_contexts = set()

        original_project = self.result.by_type("IfcProject")[0]
        project_to_add = self.result.add(model_2.by_type("IfcProject")[0])

        for element in model_2.by_type("IfcGeometricRepresentationContext"):
            new = self.result.add(element)
            self.added_contexts.add(new)
        for element in model_2:
            self.result.add(element)
        for inverse in self.result.get_inverse(project_to_add):
            ifcopenshell.util.element.replace_attribute(inverse, project_to_add, original_project)
        self.result.remove(project_to_add)
        self.reuse_existing_contexts()

        return self.patch()

    def reuse_existing_contexts(self):
        to_delete = set()

        for added_context in self.added_contexts:
            equivalent_existing_context = self.get_equivalent_existing_context(added_context)
            if equivalent_existing_context:
                for inverse in self.result.get_inverse(added_context):
                    ifcopenshell.util.element.replace_attribute(inverse, added_context, equivalent_existing_context)
                to_delete.add(added_context)

        for added_context in to_delete:
            ifcopenshell.util.element.remove_deep2(self.result, added_context)

    def get_equivalent_existing_context(self, added_context):
        for context in self.existing_contexts:
            if context.is_a() != added_context.is_a():
                continue
            if context.is_a("IfcGeometricRepresentationSubContext"):
                if (
                        context.ContextType == added_context.ContextType
                        and context.ContextIdentifier == added_context.ContextIdentifier
                        and context.TargetView == added_context.TargetView
                ):
                    return context
            elif (
                    context.ContextType == added_context.ContextType
                    and context.ContextIdentifier == added_context.ContextIdentifier
            ):
                return context


# get all the files in the folder
import os

folder = "C:/Users/FomenkoA/Desktop/ifc"
filenames = os.listdir(folder)
filepaths = [folder + "//" + file for file in filenames]
num_files = len(filepaths)

# open the files with ifcopenshell
start = datetime.now()

print(f"Finished opening files in {(datetime.now() - start).total_seconds()}s. Starting patching...")

try:
    merged_file_path = 'C:/Users/FomenkoA/Desktop/ifc/result.ifc'
    patcher = Patcher(filepaths)
    result_ifc = patcher.patch()
    result_ifc.write(merged_file_path)
    print(f"Объединённый файл сохранён по пути: {merged_file_path}")
except Exception as e:
    print(f"Произошла ошибка при объединении файлов: {e}")

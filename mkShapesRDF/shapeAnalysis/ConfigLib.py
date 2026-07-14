import os
import sys


class ConfigLib:
    @staticmethod
    def loadConfig(filesToExec, globs, imports=[]):
        """Given a list of files to execute, load them into memory

        Args:
            filesToExec (list of str): list of files to execute
            globs (globals): python globals()
            imports (list, optional): List of packages to import. If an element is tuple will do from tuple[0] import tuple[1]. Defaults to [].
        """
        for i in imports:
            if isinstance(i, str):
                exec(f"import {i}", globs, globs)
            else:
                exec(f"from {i[0]} import {i[1]}", globs, globs)
        for f in filesToExec:
            path = os.path.abspath(f)
            previous_file = globs.get("__file__")
            try:
                globs["__file__"] = path
                with open(path) as stream:
                    source = stream.read()
                exec(compile(source, path, "exec"), globs, globs)
            finally:
                if previous_file is None:
                    globs.pop("__file__", None)
                else:
                    globs["__file__"] = previous_file

    @staticmethod
    def createConfigDict(varsToKeep, objects):
        """Given all the variables stored in memory, dump the ones the user wants to keep to a dictionary
        Args:
            varsToKeep (list of str or tuple): list of variables to keep. If tuple, the first element is the name of the variable, the second is a dictionary of variables to keep inside the variable
            objects (dict): dictionary of objects in memory

        Returns:
            (dict): dictionary of variables to keep (and their subvariables)
        """

        from collections import OrderedDict

        config = OrderedDict()
        for var in varsToKeep:
            if isinstance(var, str):
                config[var] = objects[var]
            elif isinstance(var, tuple):
                d = {}
                if len(var) != 2:
                    print("Tuple should have lenght = 2! (nameOfVar, dict)")
                    sys.exit()
                for item in list(var[1].items()):
                    d[item[0]] = objects[item[1]]

                config[var[0]] = d
        return config

    @staticmethod
    def cleanConfig(varsToDelete, globs):
        for var in varsToDelete:
            if var in globs.keys():
                exec(f'del globs["{var}"]')
                del globs[var]
            else:
                del var

    @staticmethod
    def dumpConfigDict(config, filepath, doJson=False):
        if doJson:
            import json

            with open(filepath + ".json", "w") as file:
                json.dump(config, file, indent=2)
        else:
            try:
                import cloudpickle as pickle_module
            except ImportError:
                import pickle as pickle_module
            import zlib

            with open(filepath + ".pkl", "wb") as file:
                file.write(zlib.compress(pickle_module.dumps(config)))

    @staticmethod
    def dumpConfig(varsToKeep, objects, filepath):
        # given all the variables stored in memory, dump the ones the user wants to keep to a json file
        from collections import OrderedDict

        config = OrderedDict()
        for var in varsToKeep:
            if isinstance(var, str):
                config[var] = objects[var]
            elif isinstance(var, tuple):
                d = {}
                if len(var) != 2:
                    print("Tuple should have lenght = 2! (nameOfVar, dict)")
                    sys.exit()
                for item in list(var[1].items()):
                    d[item[0]] = objects[item[1]]

                config[var[0]] = d

        import json

        with open(filepath, "w") as file:
            json.dump(config, file, indent=2)

    @staticmethod
    def convertOrderedDict(d):
        return list(d.items())

    @staticmethod
    def loadDict(d, globs):
        globs["d"] = d
        for var in d.keys():
            exec(f'{var} = d["{var}"]', globs)

    @staticmethod
    def findLatestFile(folderPath, extension=".pkl"):
        import glob

        lFile = list(
            filter(
                lambda k: os.path.isfile(k), glob.glob(folderPath + "/*" + extension)
            )
        )
        lFile.sort(key=lambda x: os.path.getmtime(x))
        if len(lFile) == 0:
            print(
                f"No file found in {folderPath} with extension: {extension}\nTry compiling first with `-c 1`"
            )
            sys.exit()
        lFile = lFile[-1]
        return lFile

    @staticmethod
    def loadPickle(filePath, globs):
        try:
            import cloudpickle as pickle_module
        except ImportError:
            import pickle as pickle_module
        import zlib

        global d
        with open(filePath, "rb") as file:
            d = pickle_module.loads(zlib.decompress(file.read()))
        # ConfigLib.loadDict(globs['d'], globs)
        ConfigLib.loadDict(d, globs)
        # exec('d = d', globs)
        print(globs["batchVars"])
        return d

    @staticmethod
    def loadLatestPickle(folderPath, globs):
        lFile = ConfigLib.findLatestFile(folderPath, extension=".pkl")
        return ConfigLib.loadPickle(lFile, globs)

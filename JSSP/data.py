import csv
import re
from abc import ABC
from pathlib import Path

import numpy as np


class Task:
    """
    Task ADT.

    :type job_id: int
    :param job_id: job ID of this Task

    :type task_id: int
    :param task_id: task ID of this Task

    :type sequence: int
    :param sequence: sequence number of this Task

    :type usable_machines: 1d nparray
    :param usable_machines: usable machines that this Task can be processed on

    :type pieces: int
    :param pieces: number of pieces this Task has
    """
    def __init__(self, job_id, task_id, sequence, usable_machines, pieces):
        """
        Initializes an instance of Task.

        See help(_Task)
        """
        self._job_id = job_id
        self._task_id = task_id
        self._sequence = sequence
        self._usable_machines = usable_machines
        self._pieces = pieces

    def get_job_id(self):
        return self._job_id

    def get_task_id(self):
        return self._task_id

    def get_sequence(self):
        return self._sequence

    def get_usable_machines(self):
        return self._usable_machines

    def get_pieces(self):
        return self._pieces

    def __eq__(self, other):
        return self._job_id == other.get_job_id() \
               and self._task_id == other.get_task_id() \
               and self._sequence == other.get_sequence() \
               and np.array_equal(self._usable_machines, other.get_usable_machines())  # note pieces are omitted

    def __str__(self):
        return f"[{self._job_id}, " \
            f"{self._task_id}, " \
            f"{self._sequence}, " \
            f"{self._usable_machines}, " \
            f"{self._pieces}]"


class Job:
    """
    Job ADT.

    :type job_id: int
    :param job_id: job ID of this Job
    """
    def __init__(self, job_id):
        """
        Initializes an instance of Job.

        See help(_Job)
        """
        self._job_id = job_id
        self._tasks = []
        self._max_sequence = 0

    def set_max_sequence(self, max_sequence):
        self._max_sequence = max_sequence

    def get_max_sequence(self):
        return self._max_sequence

    def get_tasks(self):
        return self._tasks

    def get_task(self, task_id):
        return self._tasks[task_id]

    def get_job_id(self):
        return self._job_id

    def get_number_of_tasks(self):
        return len(self._tasks)

    def __eq__(self, other):
        return self._job_id == other.get_job_id() \
               and self._max_sequence == other.get_max_sequence() \
               and self._tasks == other.get_tasks()


class Data(ABC):
    """
    Base class for JSSP instance data.
    """

    def __init__(self):

        self.sequence_dependency_matrix = None
        "2d nparray of sequence dependency matrix"

        self.job_task_index_matrix = None
        "2d nparray of (job, task): index mapping"

        self.usable_machines_matrix = None
        "2d nparray of usable machines"

        self.task_processing_times_matrix = None
        "2d nparray of task processing times on machines"

        self.machine_speeds = None
        "1d nparray of machine speeds"

        self.jobs = []
        "list of all Job instances"

        self.total_number_of_jobs = 0
        self.total_number_of_tasks = 0
        self.total_number_of_machines = 0
        self.max_tasks_for_a_job = 0

    def get_setup_time(self, job1_id, job1_task_id, job2_id, job2_task_id):
        """
        Gets the setup time for scheduling (job2_id, job2_task_id) after (job1_id, job1_task_id).

        :type job1_id: int
        :param job1_id: job id of job 1

        :type job1_task_id: int
        :param job1_task_id: task id of job 1

        :type job2_id: int
        :param job2_id: job id of job 2

        :type job2_task_id: int
        :param job2_task_id: task id of job 2

        :rtype: int
        :return: setup time in minutes
        """
        if min(job1_id, job1_task_id, job2_id, job2_task_id) < 0:
            return 0

        return self.sequence_dependency_matrix[
            self.job_task_index_matrix[job1_id, job1_task_id],
            self.job_task_index_matrix[job2_id, job2_task_id]
        ]

    def get_runtime(self, job_id, task_id, machine):
        """
        Gets the run time for running (job_id, task_id) on machine.

        :type job_id: int
        :param job_id: job id

        :type task_id: int
        :param task_id: task id

        :type machine: int
        :param machine: id of machine

        :rtype: float
        :returns: run time
        """
        return self.task_processing_times_matrix[self.job_task_index_matrix[job_id, task_id], machine]

    def get_job(self, job_id):
        """
        Gets the Job with job id = job_id.

        :type job_id: int
        :param job_id: id of the Job to get

        :rtype: Job
        :returns: Job with id = job_id
        """
        return self.jobs[job_id]

    def __str__(self):
        result = f"total jobs = {self.total_number_of_jobs}\n" \
                 f"total tasks = {self.total_number_of_tasks}\n" \
                 f"total machines = {self.total_number_of_machines}\n" \
                 f"max tasks for a job = {self.max_tasks_for_a_job}\n" \
                 f"tasks:\n" \
                 f"[jobId, taskId, sequence, usable_machines, pieces]\n"

        for job in self.jobs:
            for task in job.get_tasks():
                result += str(task) + '\n'

        if self.sequence_dependency_matrix is not None:
            result += f"sequence_dependency_matrix: {self.sequence_dependency_matrix.shape}\n\n" \
                      f"{self.sequence_dependency_matrix}\n\n"

        if self.job_task_index_matrix is not None:
            result += f"dependency_matrix_index_encoding: {self.job_task_index_matrix.shape}\n\n" \
                      f"{self.job_task_index_matrix}\n\n"

        if self.usable_machines_matrix is not None:
            result += f"usable_machines_matrix: {self.usable_machines_matrix.shape}\n\n" \
                      f"{self.usable_machines_matrix}\n\n"

        if self.task_processing_times_matrix is not None:
            result += f"task_processing_times: {self.task_processing_times_matrix.shape}\n\n" \
                      f"{self.task_processing_times_matrix}\n\n"

        if self.machine_speeds is not None:
            result += f"machine_speeds: {self.machine_speeds.shape}\n\n" \
                      f"{self.machine_speeds}"

        return result

    @staticmethod
    def convert_fjs_to_csv(fjs_file, output_dir):
        """
        Converts a fjs file into three csv files, jobTasks.csv, machineRunSpeed.csv, and sequenceDependencyMatrix.csv,
        then it puts them in the output directory.

        :type fjs_file: Path | str
        :param fjs_file: path to the fjs file containing a flexible job shop schedule problem instance

        :type output_dir: Path | str
        :param output_dir: path to the directory to place the csv files into

        :returns: None
        """
        total_num_tasks = 0

        fjs_file = Path(fjs_file)
        output_dir = Path(output_dir)

        if not output_dir.exists():
            output_dir.mkdir(parents=True)

        # read .fjs input file and create jobTasks.csv
        with open(fjs_file, 'r') as fin:
            with open(output_dir / 'jobTasks.csv', 'w') as fout:
                fout.write("Job,Task,Sequence,Usable_Machines,Pieces\n")

                lines = [line for line in [l.strip() for l in fin] if line]
                line = [int(s) for s in re.sub(r'\s+', ' ', lines[0].strip()).split(' ')[:-1]]

                total_num_machines = line[1]

                # iterate over jobs
                for job_id, tasks in enumerate(lines[1:]):

                    # get the tasks data
                    task_data = [int(s) for s in re.sub(r'\s+', ' ', tasks.strip()).split(' ')]
                    total_num_tasks += task_data[0]
                    task_id = 0
                    sequence = 0

                    # iterate over tasks
                    i = 1
                    while i < len(task_data):
                        usable_machines = "["
                        output_line = f"{job_id},{task_id},{sequence},"
                        num_usable_machines = task_data[i]

                        for j in range(i + 1, i + num_usable_machines * 2 + 1, 2):
                            usable_machines += f"{task_data[j] - 1} "

                        output_line += usable_machines[:-1] + "]," + str(task_data[i + 2])
                        i += num_usable_machines * 2 + 1
                        task_id += 1
                        sequence += 1
                        fout.write(output_line + '\n')

        # create machineRunSpeed.csv
        with open(output_dir / 'machineRunSpeed.csv', 'w') as fout:
            fout.write("Machine,RunSpeed\n")
            for i in range(total_num_machines):
                fout.write(f"{i},1\n")

        # create sequenceDependencyMatrix.csv
        with open(output_dir / 'sequenceDependencyMatrix.csv', 'w') as fout:
            line = "0," * total_num_tasks + "0\n"
            for _ in range(total_num_tasks + 1):
                fout.write(line)


class CSVData(Data):
    """
    JSSP instance data class for .csv data.

    :type seq_dep_matrix_file: Path | str
    :param seq_dep_matrix_file: path to the csv file containing the sequence dependency setup times

    :type machine_speeds_file: Path | str
    :param machine_speeds_file: path to the csv file containing all of the machine speeds

    :type job_tasks_file: Path | str
    :param job_tasks_file: path to the csv file containing all of the job-tasks

    :returns: None
    """

    def __init__(self, seq_dep_matrix_file, machine_speeds_file, job_tasks_file):
        """
        Initializes all of the static data from the csv files.

        :type seq_dep_matrix_file: Path | str
        :param seq_dep_matrix_file: path to the csv file containing the sequence dependency setup times

        :type machine_speeds_file: Path | str
        :param machine_speeds_file: path to the csv file containing all of the machine speeds

        :type job_tasks_file: Path | str
        :param job_tasks_file: path to the csv file containing all of the job-tasks

        :returns: None
        """
        super().__init__()
        self.job_tasks_file_path = Path(job_tasks_file)
        self.seq_dep_matrix_file_path = Path(seq_dep_matrix_file)
        self.machine_speeds_file_path = Path(machine_speeds_file)

        self._read_job_tasks_file(self.job_tasks_file_path)
        self._read_sequence_dependency_matrix_file(self.seq_dep_matrix_file_path)
        self._read_machine_speeds_file(self.machine_speeds_file_path)

        self.total_number_of_jobs = len(self.jobs)
        self.total_number_of_tasks = self.sequence_dependency_matrix.shape[0]
        self.max_tasks_for_a_job = max([x.get_number_of_tasks() for x in self.jobs])
        self.total_number_of_machines = self.machine_speeds.shape[0]

        self.job_task_index_matrix = np.full((self.total_number_of_jobs, self.max_tasks_for_a_job), -1, dtype=np.intc)
        self.usable_machines_matrix = np.empty((self.total_number_of_tasks, self.total_number_of_machines), dtype=np.intc)
        self.task_processing_times_matrix = np.full((self.total_number_of_tasks, self.total_number_of_machines), -1, dtype=np.float)

        # process all job-tasks
        task_index = 0
        for job in self.jobs:
            for task in job.get_tasks():

                # create mapping of (job id, task id) to index
                self.job_task_index_matrix[job.get_job_id(), task.get_task_id()] = task_index

                # create row in usable_machines_matrix
                self.usable_machines_matrix[task_index] = np.resize(task.get_usable_machines(),
                                                                    self.total_number_of_machines)

                # create row in task_processing_times
                for machine in task.get_usable_machines():
                    self.task_processing_times_matrix[task_index, machine] = task.get_pieces() / self.machine_speeds[
                        machine]

                task_index += 1

    def _read_job_tasks_file(self, job_tasks_file):
        """
        Populates self.jobs by reading the job_tasks_file csv file.

        :type job_tasks_file: Path | str
        :param job_tasks_file: path to the csv file that contains the job-task data

        :returns: None

        .. Note:: this function assumes that all of the jobs in job_tasks_file are in ascending order
        and are in the same order as in the sequence_dependency_matrix csv file.
        """
        prev_job_id = -1  # record previously seen job_id
        with open(job_tasks_file) as fin:
            # skip headers (i.e. first row in csv file)
            next(fin)
            for row in csv.reader(fin):
                # create task object
                task = Task(
                    int(row[0]),  # job_id
                    int(row[1]),  # task_id
                    int(row[2]),  # seq num
                    np.array([int(x) for x in row[3][1:-1].strip().split(' ')], dtype=np.intc),  # usable machines
                    int(row[4])  # pieces
                )
                # create & append new job if we encounter job_id that has not been seen
                if task.get_job_id() != prev_job_id:
                    self.jobs.append(Job(task.get_job_id()))
                    prev_job_id = task.get_job_id()

                # update job's max sequence number
                if task.get_sequence() > self.jobs[task.get_job_id()].get_max_sequence():
                    self.jobs[task.get_job_id()].set_max_sequence(task.get_sequence())

                # append task to associated job.tasks list
                self.jobs[task.get_job_id()].get_tasks().append(task)

    def _read_sequence_dependency_matrix_file(self, seq_dep_matrix_file):
        """
        Populates self.sequence_dependency_matrix by reading the seq_dep_matrix_file csv file.

        :type seq_dep_matrix_file: Path | str
        :param seq_dep_matrix_file: path to the csv file that contains the sequence dependency matrix

        :returns: None

        .. Note:: this function assumes that all of the jobs in job_tasks_file are in ascending order
        and are in the same order as in the sequence_dependency_matrix csv file.

        """
        with open(seq_dep_matrix_file) as fin:
            # skip headers (i.e. first row in csv file)
            next(fin)
            self.sequence_dependency_matrix = np.array(
                [[int(x) for x in row[1:]]
                 for row in csv.reader(fin)], dtype=np.intc)

    def _read_machine_speeds_file(self, machine_speeds_file):
        """
        Populates self.machine_speeds by reading the machine_speeds_file csv file.

        :type machine_speeds_file: Path | str
        :param machine_speeds_file: path to the csv file that contains the machine run speeds

        :returns: None

        .. Note:: this function assumes that the machines are listed in ascending order.
        """
        with open(machine_speeds_file) as fin:
            # skip headers (i.e. first row in csv file)
            next(fin)
            self.machine_speeds = np.array([int(row[1]) for row in csv.reader(fin)], dtype=np.float)


class FJSData(Data):
    """
    JSSP instance data class for .fjs data.

    :type input_file: Path | str
    :param input_file: path to the fjs file to read the data from

    :returns: None
    """

    def __init__(self, input_file):
        """
        Initializes all of the static data from a fjs file.

        :type input_file: Path | str
        :param input_file: path to the fjs file to read the data from

        :returns: None
        """
        super().__init__()
        self.fjs_file_path = Path(input_file)
        # read .fjs input file
        with open(self.fjs_file_path, 'r') as fin:

            lines = [line for line in [l.strip() for l in fin] if line]  # read all non-blank lines
            first_line = [int(s) for s in re.sub(r'\s+', ' ', lines[0].strip()).split(' ')[:-1]]

            self.total_number_of_jobs = first_line[0]  # get total num jobs
            self.total_number_of_machines = first_line[1]  # get total num machines

            self.total_number_of_tasks = 0
            self.max_tasks_for_a_job = 0
            for line in lines[1:]:  # iterate over jobs
                # convert row (task data) to list of integers
                line = [int(s) for s in re.sub(r'\s+', ' ', line.strip()).split(' ')]

                num_tasks = int(line[0])
                self.total_number_of_tasks += num_tasks
                self.max_tasks_for_a_job = max(num_tasks, self.max_tasks_for_a_job)

            # initialize matrices
            self.task_processing_times_matrix = np.full((self.total_number_of_tasks, self.total_number_of_machines), -1,
                                                        dtype=np.float)
            self.sequence_dependency_matrix = np.zeros((self.total_number_of_tasks, self.total_number_of_tasks),
                                                       dtype=np.intc)
            self.usable_machines_matrix = np.empty((self.total_number_of_tasks, self.total_number_of_machines),
                                                   dtype=np.intc)
            self.job_task_index_matrix = np.full((self.total_number_of_jobs, self.max_tasks_for_a_job), -1,
                                                 dtype=np.intc)

            task_index = 0
            for job_id, task_data in enumerate(lines[1:]):  # iterate over jobs

                # create and append new Job
                self.jobs.append(Job(job_id))

                task_id = 0
                sequence = 0

                # get all the Job's task data
                task_data = [int(s) for s in re.sub(r'\s+', ' ', task_data.strip()).split(' ')]

                i = 1
                while i < len(task_data):  # iterate over tasks
                    num_usable_machines = task_data[i]
                    usable_machines = []

                    for j in range(i + 1, i + num_usable_machines * 2 + 1, 2):  # iterate over machines & run times for task
                        machine = task_data[j] - 1  # machines are zero indexed
                        runtime = task_data[j + 1]

                        usable_machines.append(machine)
                        self.task_processing_times_matrix[task_index, machine] = runtime

                    self.jobs[job_id].get_tasks().append(Task(job_id, task_id, sequence, usable_machines, -1))
                    self.usable_machines_matrix[task_index] = np.resize(np.array(usable_machines, dtype=np.intc),
                                                                        self.total_number_of_machines)
                    self.job_task_index_matrix[job_id, task_id] = task_index

                    task_id += 1
                    sequence += 1
                    task_index += 1
                    i += num_usable_machines * 2 + 1

                self.jobs[job_id].set_max_sequence(sequence - 1)

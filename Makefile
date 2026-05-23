# We use a branch of Speckle (https://github.com/ccelio/Speckle) to cross
# compile the binaries for SPEC CPU 2026. These can be compiled locally on a
# machine with the SPEC CPU 2026 installation, and the overlay directories
# ($(SPECKLE_DIR)/build/overlay) can be moved to EC2.

# Default to the submodule.
SPECKLE_DIR ?= Speckle

# Default to ref input size for SPEC CPU 2026.
INPUT ?= ref

# Optional single benchmark build:
#   make spec-benchmark SUITE=fpspeed BENCHMARK=803.sph_exa_s
#   make spec-commands-benchmark SUITE=fpspeed BENCHMARK=803.sph_exa_s
SUITE ?=
BENCHMARK ?=

spec_suites = intrate intspeed fprate fpspeed
spec_rootfs_dirs = $(patsubst %, spec-%, $(spec_suites))
spec_command_dirs = $(patsubst %, spec-commands-%, $(spec_suites))
.PHONY: FORCE
FORCE:

.PHONY: spec-intrate spec-intspeed spec-fprate spec-fpspeed
.PHONY: spec-commands-intrate spec-commands-intspeed spec-commands-fprate spec-commands-fpspeed
.PHONY: spec-clean-overlay spec-all spec-commands spec-commands-benchmark spec-benchmark clean

spec-commands-intrate: FORCE
	cd $(SPECKLE_DIR) && ./gen_binaries.sh --genCommands --suite intrate --input $(INPUT)

spec-commands-intspeed: FORCE
	cd $(SPECKLE_DIR) && ./gen_binaries.sh --genCommands --suite intspeed --input $(INPUT)

spec-commands-fprate: FORCE
	cd $(SPECKLE_DIR) && ./gen_binaries.sh --genCommands --suite fprate --input $(INPUT)

spec-commands-fpspeed: FORCE
	cd $(SPECKLE_DIR) && ./gen_binaries.sh --genCommands --suite fpspeed --input $(INPUT)

spec-clean-overlay: FORCE
	rm -rf $(SPECKLE_DIR)/build/overlay

spec-intrate: FORCE spec-commands-intrate spec-clean-overlay
	cd $(SPECKLE_DIR) && ./gen_binaries.sh --compile --suite intrate --input $(INPUT)
	echo $(SPECKLE_DIR)/build/overlay/intrate/$(INPUT)

spec-intspeed: FORCE spec-commands-intspeed spec-clean-overlay
	cd $(SPECKLE_DIR) && ./gen_binaries.sh --compile --suite intspeed --input $(INPUT)
	echo $(SPECKLE_DIR)/build/overlay/intspeed/$(INPUT)

spec-fprate: FORCE spec-commands-fprate spec-clean-overlay
	cd $(SPECKLE_DIR) && ./gen_binaries.sh --compile --suite fprate --input $(INPUT)
	echo $(SPECKLE_DIR)/build/overlay/fprate/$(INPUT)

spec-fpspeed: FORCE spec-commands-fpspeed spec-clean-overlay
	cd $(SPECKLE_DIR) && ./gen_binaries.sh --compile --suite fpspeed --input $(INPUT)
	echo $(SPECKLE_DIR)/build/overlay/fpspeed/$(INPUT)

spec-commands: spec-commands-intrate spec-commands-intspeed spec-commands-fprate spec-commands-fpspeed

spec-all: spec-clean-overlay spec-intrate spec-intspeed spec-fprate spec-fpspeed

spec-commands-benchmark: FORCE
	@test -n "$(SUITE)" || { echo "ERROR: set SUITE=<intrate|intspeed|fprate|fpspeed>"; exit 1; }
	@test -n "$(BENCHMARK)" || { echo "ERROR: set BENCHMARK=<benchmark>, e.g. 803.sph_exa_s"; exit 1; }
	cd $(SPECKLE_DIR) && ./gen_binaries.sh --genCommands --suite $(SUITE) --input $(INPUT) --benchmark $(BENCHMARK)

spec-benchmark: FORCE spec-commands-benchmark spec-clean-overlay
	@test -n "$(SUITE)" || { echo "ERROR: set SUITE=<intrate|intspeed|fprate|fpspeed>"; exit 1; }
	@test -n "$(BENCHMARK)" || { echo "ERROR: set BENCHMARK=<benchmark>, e.g. 803.sph_exa_s"; exit 1; }
	cd $(SPECKLE_DIR) && ./gen_binaries.sh --compile --suite $(SUITE) --input $(INPUT) --benchmark $(BENCHMARK)
	echo $(SPECKLE_DIR)/build/overlay/$(SUITE)/$(INPUT)/$(BENCHMARK)

clean:
	rm -rf $(SPECKLE_DIR)/build
	
clean-overlay:
	rm -rf $(SPECKLE_DIR)/build/overlay

.PHONY: \
	spec-intrate \
	spec-intspeed \
	spec-fprate \
	spec-fpspeed \
	$(spec_command_dirs) \
	spec-commands \
	spec-clean-overlay \
	spec-all \
	spec-commands-benchmark \
	spec-benchmark \
	clean
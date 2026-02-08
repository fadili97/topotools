#!/bin/bash

# ELFADILY TopoTools - Release Helper Script
# Usage: ./release.sh 1.2.0 "Description of changes"

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if version is provided
if [ -z "$1" ]; then
    echo -e "${RED}❌ Error: Version number required${NC}"
    echo "Usage: ./release.sh <version> [description]"
    echo "Example: ./release.sh 1.2.0 \"Added new features\""
    exit 1
fi

VERSION=$1
DESCRIPTION=${2:-"Release version $VERSION"}
TAG="v$VERSION"
METADATA_FILE="elfadily_topotools/metadata.txt"

echo -e "${YELLOW}🚀 ELFADILY TopoTools Release Process${NC}"
echo "Version: $VERSION"
echo "Description: $DESCRIPTION"
echo ""

# Check if metadata file exists
if [ ! -f "$METADATA_FILE" ]; then
    echo -e "${RED}❌ Error: $METADATA_FILE not found${NC}"
    exit 1
fi

# Check if git repo
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ Error: Not a git repository${NC}"
    exit 1
fi

# Check for uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}⚠️  Warning: You have uncommitted changes${NC}"
    echo -e "${YELLOW}   Commit them first or stash them${NC}"
    git status --short
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update version in metadata.txt
echo -e "${GREEN}📝 Updating metadata.txt...${NC}"
sed -i "s/^version=.*/version=$VERSION/" "$METADATA_FILE"

# Show the change
echo "New version line:"
grep "^version=" "$METADATA_FILE"

# Commit the version change
echo -e "${GREEN}💾 Committing version bump...${NC}"
git add "$METADATA_FILE"
git commit -m "Bump version to $VERSION - $DESCRIPTION"

# Create and push tag
echo -e "${GREEN}🏷️  Creating tag $TAG...${NC}"
git tag -a "$TAG" -m "Release $VERSION: $DESCRIPTION"

# Push to remote
echo -e "${GREEN}⬆️  Pushing to GitHub...${NC}"
git push origin main
git push origin "$TAG"

echo ""
echo -e "${GREEN}✅ Release process completed!${NC}"
echo ""
echo "Next steps:"
echo "1. Check GitHub Actions: https://github.com/elfadily-geoconseil/topotools/actions"
echo "2. Verify release: https://github.com/elfadily-geoconseil/topotools/releases"
echo "3. Check XML feed (wait 2-5 min): https://elfadily-geoconseil.github.io/topotools/plugins.xml"
echo ""
echo -e "${YELLOW}📦 Team members will receive update notification in QGIS${NC}"
